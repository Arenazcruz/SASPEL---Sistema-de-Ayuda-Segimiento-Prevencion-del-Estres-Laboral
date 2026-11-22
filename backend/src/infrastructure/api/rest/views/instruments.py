"""T25-A: reutiliza autenticación JWT y permisos SUPERADMIN de todo el módulo."""

from dataclasses import asdict
from rest_framework.response import Response
from src.application.dto.instruments import InstrumentData, InstrumentFilters
from src.application.use_cases import instruments as cases
from src.infrastructure.api.rest.serializers.instruments import InstrumentFilterSerializer, InstrumentSerializer, InstrumentRequestSerializer
from src.infrastructure.api.rest.views.superadmin import SuperadminView
from src.infrastructure.dependencies.instruments import build_instruments


class InstrumentsView(SuperadminView):
    def get(self, request):
        filters = InstrumentFilters(**self.validated(InstrumentFilterSerializer, request.query_params.dict()))
        return Response(asdict(build_instruments(cases.ListInstruments).execute(filters)))

    def post(self, request):
        data = InstrumentData(**self.validated(InstrumentSerializer, request.data))
        return Response(asdict(build_instruments(cases.CreateInstrument).execute(data)), status=201)


class InstrumentDetailView(SuperadminView):
    def get(self, request, instrument_id):
        return Response(asdict(build_instruments(cases.GetInstrument).execute(instrument_id)))

    def patch(self, request, instrument_id):
        changes = self.validated(InstrumentSerializer, request.data, partial=True)
        return Response(asdict(build_instruments(cases.EditInstrument).execute(instrument_id, changes)))


class InstrumentStateView(SuperadminView):
    def post(self, request, instrument_id, active):
        self.validated(InstrumentRequestSerializer, request.data)
        return Response(asdict(build_instruments(cases.SetInstrumentActive).execute(instrument_id, active)))
