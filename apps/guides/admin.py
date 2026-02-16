from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from apps.guides.models import Guide, GuideAvailability
from apps.scheduling.models import RestaurantStaff as BaseRestaurantStaff


class GuideInline(admin.StackedInline):
    model = Guide
    can_delete = True
    verbose_name_plural = 'Guide Profile (Optional - only fill if this user is a tour guide)'
    fields = ['guide_type', 'phone', 'is_active']
    extra = 0
    max_num = 1

    def has_add_permission(self, request, obj=None):
        # Only show "Add another" if no guide profile exists
        if obj and hasattr(obj, 'guide_profile'):
            return False
        return True


class RestaurantStaffInline(admin.StackedInline):
    model = BaseRestaurantStaff
    can_delete = True
    verbose_name_plural = 'Restaurant Staff Profile (Optional - only fill if this user is kitchen/serving staff)'
    fields = ['staff_type', 'is_active', 'hire_date']
    extra = 0
    max_num = 1

    def has_add_permission(self, request, obj=None):
        # Only show "Add another" if no restaurant staff profile exists
        if obj and hasattr(obj, 'restaurant_staff'):
            return False
        return True


class CustomUserAdmin(UserAdmin):
    inlines = [GuideInline, RestaurantStaffInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_profile_type']
    list_filter = ['is_staff', 'is_superuser', 'is_active']

    def get_profile_type(self, obj):
        profiles = []
        try:
            guide_type = obj.guide_profile.get_guide_type_display()
            profiles.append(f"Guide: {guide_type}")
        except Guide.DoesNotExist:
            pass

        try:
            staff_type = obj.restaurant_staff.get_staff_type_display()
            profiles.append(f"Staff: {staff_type}")
        except BaseRestaurantStaff.DoesNotExist:
            pass

        return ', '.join(profiles) if profiles else 'No profile'

    get_profile_type.short_description = 'Profile Type'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'guide_type', 'phone', 'is_active', 'created_at']
    list_filter = ['guide_type', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('User Information', {
            'fields': ['user']
        }),
        ('Guide Details', {
            'fields': ['guide_type', 'phone', 'is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__first_name'


@admin.register(GuideAvailability)
class GuideAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['guide', 'date', 'is_available', 'notes', 'created_at']
    list_filter = ['is_available', 'date']
    search_fields = ['guide__user__username', 'guide__user__first_name', 'guide__user__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['guide', 'date', 'is_available', 'notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('guide__user')
