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
from django.http import JsonResponse
from django.core.management import call_command



class SeedDatabaseView(APIView):
    def get(self, request):
        try:
            call_command('seed_profiles')
            return JsonResponse({"status": "success", "message": "Database seeded"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50
    page_query_param = 'page'

# List view with filtering, sorting, pagination
class ProfileListView(APIView):
    def get(self, request):
        # Filtering
        filterset = ProfileFilter(request.GET, queryset=Profile.objects.all())
        if not filterset.is_valid():
            return Response(
                {"status": "error", "message": "Invalid query parameters"},
                status=status.HTTP_400_BAD_REQUEST,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        queryset = filterset.qs

        # Sorting validation
        sort_by = request.GET.get('sort_by')
        order = request.GET.get('order', 'asc')
        allowed_sort_fields = ['age', 'created_at', 'gender_probability']
        if sort_by and sort_by not in allowed_sort_fields:
            return Response(
                {"status": "error", "message": "Invalid query parameters"},
                status=status.HTTP_400_BAD_REQUEST,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        if order not in ['asc', 'desc']:
            return Response(
                {"status": "error", "message": "Invalid query parameters"},
                status=status.HTTP_400_BAD_REQUEST,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Apply sorting
        if sort_by:
            if order == 'desc':
                sort_by = f'-{sort_by}'
            queryset = queryset.order_by(sort_by)

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProfileListSerializer(page, many=True)

        return Response({
            "status": "success",
            "page": paginator.page.number,
            "limit": paginator.page_size,
            "total": queryset.count(),
            "data": serializer.data
        }, headers={"Access-Control-Allow-Origin": "*"})
# Natural language search
class NaturalLanguageSearchView(APIView):
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

        return Response({
            "status": "success",
            "page": paginator.page.number,
            "limit": paginator.page_size,
            "total": queryset.count(),
            "data": serializer.data
        }, headers={"Access-Control-Allow-Origin": "*"})

# Single profile detail view (already exists, keep as is)
class ProfileDetailView(APIView):
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