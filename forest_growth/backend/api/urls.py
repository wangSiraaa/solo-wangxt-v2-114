from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisRunViewSet, EquationReleaseViewSet, IdentityReviewViewSet,
    PlotViewSet, RemeasurePreviewViewSet, StratumViewSet, SurveyViewSet,
    TagCrosswalkViewSet, TreeRecordViewSet,
)

router = DefaultRouter()
router.register("strata", StratumViewSet)
router.register("plots", PlotViewSet)
router.register("surveys", SurveyViewSet)
router.register("trees", TreeRecordViewSet)
router.register("crosswalks", TagCrosswalkViewSet)
router.register("reviews", IdentityReviewViewSet)
router.register("equation-releases", EquationReleaseViewSet)
router.register("analysis-runs", AnalysisRunViewSet)

urlpatterns = [
    path("remeasure-preview/",
         RemeasurePreviewViewSet.as_view({"get": "list"}),
         name="remeasure-preview"),
    path("", include(router.urls)),
]
