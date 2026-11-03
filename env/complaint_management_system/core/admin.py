from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Complaint_category, Department, Complaint, ComplaintResponse, ComplaintStatusHistory

# 1. Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "email_verified", "is_staff", "is_active", "department", "campus")
    list_filter = ("role", "email_verified", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + ((None, {"fields": ("role", "email_verified", "email_verified_at")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + ((None, {"fields": ("role", "email_verified", "email_verified_at",'department','campus')}),)

# 2. Complaint Category Admin
@admin.register(Complaint_category)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "description")

# 3. Department Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")

# Inline classes for the Complaint View
class ComplaintResponseInline(admin.TabularInline):
    model = ComplaintResponse
    extra = 1
    fields = ("responder", "remarks", "is_internal", "created_at")
    readonly_fields = ("created_at",)

class ComplaintStatusHistoryInline(admin.TabularInline):
    model = ComplaintStatusHistory
    extra = 0
    fields = ("changed_by", "old_status", "new_status", "note", "created_at")
    readonly_fields = ("changed_by", "old_status", "new_status", "note", "created_at")
    can_delete = False

# 4. Complaint Admin
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("complaint_no", "title", "user", "category", "department", "assigned_to", "status", "priority", "created_at")
    list_filter = ("status", "priority", "category", "department", "created_at")
    search_fields = ("complaint_no", "title", "description", "user__username")
    readonly_fields = ("complaint_no", "created_at", "updated_at", "resolved_at")
    inlines = [ComplaintResponseInline, ComplaintStatusHistoryInline]

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Complaint.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                ComplaintStatusHistory.objects.create(complaint=obj, changed_by=request.user, old_status=old_obj.status, new_status=obj.status, note="Status updated via admin panel.")
        super().save_model(request, obj, form, change)

# 5. Complaint Response Admin
@admin.register(ComplaintResponse)
class ComplaintResponseAdmin(admin.ModelAdmin):
    list_display = ("complaint", "responder", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at")
    search_fields = ("complaint__complaint_no", "responder__username", "remarks")

# 6. Complaint Status History Admin
@admin.register(ComplaintStatusHistory)
class ComplaintStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("complaint", "changed_by", "old_status", "new_status", "created_at")
    list_filter = ("old_status", "new_status", "created_at")
    search_fields = ("complaint__complaint_no", "changed_by__username")
    readonly_fields = ("complaint", "changed_by", "old_status", "new_status", "note", "created_at")

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

