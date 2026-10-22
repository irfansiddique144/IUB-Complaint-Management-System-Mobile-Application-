import uuid
from pathlib import Path
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

# Generate unique complaint numbers automatically
def generate_complaint_no():
    return f"CMS-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"

# Validate uploaded attachment size (5 MB maximum)
def validate_attachment_size(file):
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError("Attachment size cannot exceed 5 MB.")

# 1. Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [("admin", "Admin"), ("user", "User")]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user", db_index=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# 2. Complaint Category Model
class Complaint_category(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("inactive", "Inactive")]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Complaint Category"
        verbose_name_plural = "Complaint Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

# 3. Department Model
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

# 4. Complaint Model
class Complaint(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("in_progress", "In Progress"), ("resolved", "Resolved"), ("rejected", "Rejected")]
    PRIORITY_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")]

    complaint_no = models.CharField(max_length=30, unique=True, default=generate_complaint_no, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="complaints")
    category = models.ForeignKey(Complaint_category, on_delete=models.PROTECT, related_name="complaints")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="complaints", blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="assigned_complaints", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium", db_index=True)
    attachment = models.FileField(upload_to="complaint_attachments/", validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"]), validate_attachment_size], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["department", "status"]),
        ]

    def save(self, *args, **kwargs):
        if self.status == "resolved":
            if self.resolved_at is None:
                self.resolved_at = timezone.now()
        else:
            self.resolved_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.complaint_no} - {self.title}"

# 5. Complaint Response Model
class ComplaintResponse(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="responses")
    responder = models.ForeignKey(User, on_delete=models.PROTECT, related_name="complaint_responses")
    remarks = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal notes are visible only to authorized staff.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Response to {self.complaint.complaint_no} by {self.responder.username}"

# 6. Complaint Status History Model
class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="complaint_status_changes")
    old_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Complaint Status History"
        verbose_name_plural = "Complaint Status Histories"

    def __str__(self):
        return f"{self.complaint.complaint_no}: {self.old_status} -> {self.new_status}"
