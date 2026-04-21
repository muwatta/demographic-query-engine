# Demographic Query Engine – HNG Stage 2

## API Endpoints

### GET /api/profiles/
Supports filtering, sorting, pagination.

**Filters**: gender, age_group, country_id, min_age, max_age, min_gender_probability, min_country_probability

**Sorting**: sort_by=age|created_at|gender_probability, order=asc|desc

**Pagination**: page (default 1), limit (default 10, max 50)

Example: `/api/profiles/?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10`

### GET /api/profiles/search?q=<query>
Natural language search.

Examples:
- `?q=young males from nigeria`
- `?q=females above 30`
- `?q=adult males from kenya`

### GET /api/profiles/<uuid>/
Get a single profile.

### DELETE /api/profiles/<uuid>/
Delete a profile.

## Natural Language Parsing Approach

- **Rule-based, no AI/LLM**.
- **Keywords supported**:
  - Gender: `male`, `female`
  - Age group: `child`, `teenager`, `adult`, `senior`
  - Special: `young` → age 16-24
  - Numeric: `above X`, `below X`, `between X and Y`
  - Country names: `nigeria`, `kenya`, `south africa`, `ghana`, `angola`, `ethiopia`, `morocco`, `egypt`, `tanzania`, `uganda`, `rwanda`, `congo`, `cameroon`, `senegal`

- **Mapping logic**: Extracted keywords are converted into database filters. Multiple filters are combined with AND.

- **Limitations**:
  - Does not support negation (e.g., "not male").
  - Cannot handle complex sentence structures or synonyms.
  - Country list is limited to predefined names.
  - Age ranges for "young" are fixed (16-24) and not configurable.
  - No support for name‑based or probability‑based natural queries.

## Deployment
Live at: https://demographic-query-engine.vercel.app (replace with your actual URL)

## Local Setup
1. Clone repo
2. Create virtual environment
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py seed_profiles`
6. `python manage.py runserver`