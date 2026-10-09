from dataclasses import asdict
from uuid import UUID
from rest_framework.response import Response

from src.application.dto.instrument_content import ContentFilters
from src.application.use_cases.instrument_content import DATA_TYPES
from src.infrastructure.api.rest.serializers.instrument_content import (
    CONTENT_SERIALIZERS, ContentFilterSerializer, MoveContentSerializer,
)
from src.infrastructure.api.rest.serializers.instruments import InstrumentRequestSerializer
from src.infrastructure.api.rest.views.superadmin import SuperadminView
from src.infrastructure.dependencies.instrument_content import build_content


class ContentListView(SuperadminView):
    def get(self, request, kind, parent_id: UUID | None = None):
        filters = ContentFilters(**self.validated(ContentFilterSerializer, request.query_params.dict()))
        return Response(asdict(build_content().list(kind, parent_id, filters)))

    def post(self, request, kind, parent_id: UUID | None = None):
        data = DATA_TYPES[kind](**self.validated(CONTENT_SERIALIZERS[kind], request.data))
        return Response(asdict(build_content().create(kind, parent_id, data)), status=201)


class ContentDetailView(SuperadminView):
    def get(self, request, kind, item_id: UUID, parent_id: UUID | None = None):
        return Response(asdict(build_content().get(kind, parent_id, item_id)))

    def patch(self, request, kind, item_id: UUID, parent_id: UUID | None = None):
        changes = self.validated(CONTENT_SERIALIZERS[kind], request.data, partial=True)
        return Response(asdict(build_content().edit(kind, parent_id, item_id, changes)))


class ContentActionView(SuperadminView):
    def post(self, request, kind, item_id: UUID, action, parent_id: UUID | None = None):
        if action == 'move':
            data = self.validated(MoveContentSerializer, request.data)
            result = build_content().move(kind, parent_id, item_id, data['direction'])
        else:
            self.validated(InstrumentRequestSerializer, request.data)
            result = build_content().set_active(kind, parent_id, item_id, action == 'activate')
        return Response(asdict(result))
