from django.contrib.gis import admin

from .models import (
    AnalysisRun, EquationReleaseModel, IdentityReview, Plot, PlotSurvey,
    Stratum, Survey, TagCrosswalk, TreeRecord,
)


@admin.register(Stratum)
class StratumAdmin(admin.GISModelAdmin):
    list_display = ("code", "name", "area_ha")


@admin.register(Plot)
class PlotAdmin(admin.GISModelAdmin):
    list_display = ("plot_id", "stratum", "area_ha")
    list_filter = ("stratum",)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("survey_no", "survey_date", "status", "approved_by")
    list_filter = ("status",)


@admin.register(TreeRecord)
class TreeRecordAdmin(admin.GISModelAdmin):
    list_display = ("plot", "survey", "tag", "species_code", "status",
                    "dbh_value", "dbh_unit", "height_value", "height_unit")
    list_filter = ("survey", "plot", "species_code", "status")
    search_fields = ("tag",)


admin.site.register(PlotSurvey, admin.GISModelAdmin)
admin.site.register(TagCrosswalk)
admin.site.register(IdentityReview)
admin.site.register(EquationReleaseModel)
admin.site.register(AnalysisRun)
