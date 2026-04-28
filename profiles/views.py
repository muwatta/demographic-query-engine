from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .models import Profile
from .serializers import ProfileListSerializer, ProfileDetailSerializer
from .filters import ProfileFilter
from .nlp_parser import parse_query
from django.http import JsonResponse, HttpResponse
from django.core.management import call_command
import csv
from datetime import datetime
from users.permissions import IsAdmin, IsAnalyst

def health_check(request):
    return JsonResponse({"status": "ok", "database_connected": Profile.objects.exists()})

# Pagination with required envelope (total_pages + links)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'status': 'success',
            'page': self.page.number,
            'limit': self.page.paginator.per_page,
            'total': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'links': {
                'self': self.request.build_absolute_uri(),
                'next': self.get_next_link(),
                'prev': self.get_previous_link(),
            },
            'data': data
        })

# Profile list – now uses DRF's ListAPIView for clean pagination
from rest_framework.generics import ListAPIView
class ProfileListView(ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProfileFilter
    ordering_fields = ['age', 'created_at', 'gender_probability']
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAnalyst]

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.query_params.get('sort_by')
        order = self.request.query_params.get('order', 'asc')
        if sort_by in self.ordering_fields:
            if order == 'desc':
                sort_by = f'-{sort_by}'
            queryset = queryset.order_by(sort_by)
        return queryset

# Natural language search – keep custom logic but use same pagination envelope
class NaturalLanguageSearchView(APIView):
    permission_classes = [IsAnalyst]

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q:
            return Response(
                {"status": "error", "message": "Missing or empty query"},
                status=status.HTTP_400_BAD_REQUEST,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        filters = parse_query(q)
        if filters is None:
            return Response(
                {"status": "error", "message": "Unable to interpret query"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        queryset = Profile.objects.all()
        if 'gender' in filters:
            queryset = queryset.filter(gender=filters['gender'])
        if 'age_group' in filters:
            queryset = queryset.filter(age_group=filters['age_group'])
        if 'min_age' in filters:
            queryset = queryset.filter(age__gte=filters['min_age'])
        if 'max_age' in filters:
            queryset = queryset.filter(age__lte=filters['max_age'])
        if 'country_id' in filters:
            queryset = queryset.filter(country_id=filters['country_id'])

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProfileListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProfileCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'status': 'error', 'message': 'name required'}, status=400)
        # Assume you have the get_name_data function from Stage 1
        from .services import get_name_data
        try:
            data = get_name_data(name)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=502)
        profile = Profile.objects.create(name=name, **data)
        serializer = ProfileDetailSerializer(profile)
        return Response({'status': 'success', 'data': serializer.data}, status=201)

# Single profile detail view – both admin and analyst can read, only admin can delete
class ProfileDetailView(APIView):
    permission_classes = [IsAnalyst]

    def get(self, request, id):
        try:
            profile = Profile.objects.get(id=id)
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        serializer = ProfileDetailSerializer(profile)
        return Response({
            "status": "success",
            "data": serializer.data
        }, headers={"Access-Control-Allow-Origin": "*"})

    def delete(self, request, id):
        if request.user.role != 'admin':
            return Response(
                {"status": "error", "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        try:
            profile = Profile.objects.get(id=id)
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT, headers={"Access-Control-Allow-Origin": "*"})

# CSV export
class ProfileExportView(APIView):
    permission_classes = [IsAnalyst]

    def get(self, request):
        filterset = ProfileFilter(request.GET, queryset=Profile.objects.all())
        if not filterset.is_valid():
            return Response({'status': 'error', 'message': 'Invalid filters'}, status=400)
        queryset = filterset.qs

        # apply sorting if any
        sort_by = request.GET.get('sort_by')
        order = request.GET.get('order', 'asc')
        if sort_by in ['age', 'created_at', 'gender_probability']:
            if order == 'desc':
                sort_by = f'-{sort_by}'
            queryset = queryset.order_by(sort_by)

        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response['Content-Disposition'] = f'attachment; filename="profiles_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'name', 'gender', 'gender_probability', 'age', 'age_group',
                         'country_id', 'country_name', 'country_probability', 'created_at'])
        for p in queryset:
            writer.writerow([p.id, p.name, p.gender, p.gender_probability,
                             p.age, p.age_group, p.country_id, p.country_name,
                             p.country_probability, p.created_at.isoformat()])
        return response