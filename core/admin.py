from django.contrib import admin
from .models import TKResources, Status, Framework, FrameworkRequirement, InternalControl, Audit, AuditAssessment, Finding

@admin.register(TKResources)
class TKResourcesAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(InternalControl)
class InternalControlAdmin(admin.ModelAdmin):
    list_display = ('wp_ref', 'short_description')
    search_fields = ('wp_ref', 'short_description')
    autocomplete_fields = ['requirements']

@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_year')
    search_fields = ('name',)

@admin.register(AuditAssessment)
class AuditAssessmentAdmin(admin.ModelAdmin):
    list_display = ('audit', 'control', 'status', 'tester')
    autocomplete_fields = ['control', 'tester', 'reviewer', 'audit']

@admin.register(FrameworkRequirement)
class FrameworkRequirementAdmin(admin.ModelAdmin):
    list_display = ('code', 'short_description', 'framework', 'parent')
    search_fields = ('code', 'short_description') 
    list_filter = ('framework',)
    autocomplete_fields = ['parent']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Determine the source of the search request
        # 'model_name' tells us which page the user is currently on
        referring_model = request.GET.get('model_name')

        if referring_model == 'frameworkrequirement':
            # We are on the Requirement page: Only show Top-Level Parents
            queryset = queryset.filter(parent__isnull=True)
        
        # If referring_model is 'internalcontrol', we don't filter.
        # This allows you to see both CC6.1 AND 6.1.1 (the Points of Focus).
            
        return queryset, use_distinct

# Register the rest
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    search_fields = ('status_name', 'type')

admin.site.register(Framework)
admin.site.register(Finding)
