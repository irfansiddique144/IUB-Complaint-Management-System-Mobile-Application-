from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import Complaint, Complaint_category, Department, ComplaintResponse, ComplaintStatusHistory
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
User = get_user_model()

# Helper function to check if user is admin/staff
def is_admin(user):
    return user.role == 'admin' or user.is_staff

# ==========================================
# 1. COMPLAINT CATEGORY VIEWS
# ==========================================

class ComplaintCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = list(Complaint_category.objects.filter(status='active').values('id', 'name', 'description'))
        return Response(categories, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        
        if not name:
            return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            category = Complaint_category.objects.create(name=name, description=description)
            return Response({'id': category.id, 'name': category.name, 'description': category.description}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ComplaintCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            category = Complaint_category.objects.get(pk=pk)
            return Response({'id': category.id, 'name': category.name, 'description': category.description, 'status': category.status})
        except Complaint_category.DoesNotExist:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            category = Complaint_category.objects.get(pk=pk)
        except Complaint_category.DoesNotExist:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)

        category.name = request.data.get('name', category.name)
        category.description = request.data.get('description', category.description)
        category.status = request.data.get('status', category.status)
        
        try:
            category.save()
            return Response({'id': category.id, 'name': category.name, 'description': category.description, 'status': category.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            category = Complaint_category.objects.get(pk=pk)
            category.delete()
            return Response({'message': 'Category deleted successfully.'}, status=status.HTTP_200_OK)
        except Complaint_category.DoesNotExist:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)


# ==========================================
# 2. DEPARTMENT VIEWS
# ==========================================

class DepartmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = list(Department.objects.filter(is_active=True).values('id', 'name', 'description'))
        return Response(departments, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')

        if not name:
            return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dept = Department.objects.create(name=name, description=description)
            return Response({'id': dept.id, 'name': dept.name, 'description': dept.description}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
            return Response({'id': dept.id, 'name': dept.name, 'description': dept.description, 'is_active': dept.is_active})
        except Department.DoesNotExist:
            return Response({'error': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)

        dept.name = request.data.get('name', dept.name)
        dept.description = request.data.get('description', dept.description)
        dept.is_active = request.data.get('is_active', dept.is_active)

        try:
            dept.save()
            return Response({'id': dept.id, 'name': dept.name, 'description': dept.description, 'is_active': dept.is_active})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
            dept.delete()
            return Response({'message': 'Department deleted successfully.'}, status=status.HTTP_200_OK)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)


# ==========================================
# 3. COMPLAINT VIEWS
# ==========================================

class ComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Check the user's role to determine what they should see
        # Adjust 'admin' to match whatever you named your admin role in the User model
        if request.user.role == 'admin' or request.user.is_staff:
            queryset = Complaint.objects.all()
        else:
            # 2. Filter complaints to ONLY match the currently authenticated user
            queryset = Complaint.objects.filter(user=request.user)

        complaints = []
        for c in queryset:
            complaints.append({
                'id': c.id,
                'complaint_no': c.complaint_no,
                'user': c.user.username,
                'category': c.category.name,
                'department': c.department.name if c.department else None,
                'assigned_to': c.assigned_to.username if c.assigned_to else None,
                'title': c.title,
                'description': c.description,
                'status': c.status,
                'priority': c.priority,
                'attachment': c.attachment.url if c.attachment else None,
                'created_at': c.created_at.isoformat()
            })
        return Response(complaints, status=status.HTTP_200_OK)

    def post(self, request):
        # DRF's request.data seamlessly handles BOTH standard JSON and Multi-part Form Data (Files)
        title = request.data.get('title')
        description = request.data.get('description')
        category_id = request.data.get('category_id')
        department_id = request.data.get('department_id')
        priority = request.data.get('priority', 'medium')
        attachment = request.data.get('attachment')

        if not all([title, description, category_id]):
            return Response({'error': 'title, description, and category_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = Complaint_category.objects.get(pk=category_id)
            department = Department.objects.get(pk=department_id) if department_id else None
            
            complaint = Complaint.objects.create(
                user=request.user,  # Securely use the authenticated user instead of a passed user_id
                category=category,
                department=department,
                title=title,
                description=description,
                priority=priority,
                attachment=attachment
            )
            return Response({
                'id': complaint.id,
                'complaint_no': complaint.complaint_no,
                'title': complaint.title,
                'status': complaint.status
            }, status=status.HTTP_201_CREATED)
            
        except (Complaint_category.DoesNotExist, Department.DoesNotExist) as e:
            return Response({'error': f'Invalid Foreign Key Reference: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # Helper method to fetch the complaint and check ownership permissions
    def get_object(self, pk, user):
        try:
            complaint = Complaint.objects.get(pk=pk)
            # Security Check: Only allow if it's their complaint, or they are an admin
            if complaint.user != user and not is_admin(user):
                return None
            return complaint
        except Complaint.DoesNotExist:
            return None

    def get(self, request, pk):
        complaint = self.get_object(pk, request.user)
        if not complaint:
            return Response({'error': 'Complaint not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            'id': complaint.id,
            'complaint_no': complaint.complaint_no,
            'user': complaint.user.username,
            'category': complaint.category.name,
            'department': complaint.department.name if complaint.department else None,
            'assigned_to': complaint.assigned_to.username if complaint.assigned_to else None,
            'title': complaint.title,
            'description': complaint.description,
            'status': complaint.status,
            'priority': complaint.priority,
            'attachment': complaint.attachment.url if complaint.attachment else None,
            'created_at': complaint.created_at.isoformat(),
            'resolved_at': complaint.resolved_at.isoformat() if complaint.resolved_at else None
        }, status=status.HTTP_200_OK)
        
    def put(self, request, pk):
        complaint = self.get_object(pk, request.user)
        if not complaint:
            return Response({'error': 'Complaint not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        complaint.title = request.data.get('title', complaint.title)
        complaint.description = request.data.get('description', complaint.description)
        complaint.status = request.data.get('status', complaint.status)
        complaint.priority = request.data.get('priority', complaint.priority)

        category_id = request.data.get('category_id')
        department_id = request.data.get('department_id')
        assigned_to_id = request.data.get('assigned_to_id')

        try:
            if category_id:
                complaint.category = Complaint_category.objects.get(pk=category_id)
            if department_id is not None:
                complaint.department = Department.objects.get(pk=department_id) if department_id else None
            # Only admins should be able to assign tickets to specific users
            if assigned_to_id is not None and is_admin(request.user):
                complaint.assigned_to = User.objects.get(pk=assigned_to_id) if assigned_to_id else None

            complaint.save()
            return Response({
                'id': complaint.id,
                'complaint_no': complaint.complaint_no,
                'title': complaint.title,
                'status': complaint.status,
                'priority': complaint.priority
            }, status=status.HTTP_200_OK)
        except (User.DoesNotExist, Complaint_category.DoesNotExist, Department.DoesNotExist) as e:
            return Response({'error': f'Invalid Foreign Key Reference: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        complaint = self.get_object(pk, request.user)
        if not complaint:
            return Response({'error': 'Complaint not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            complaint.delete()
            return Response({'message': 'Complaint deleted successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# ==========================================
# 4. USER VIEWS
# ==========================================
class UserView(APIView):
    # Allow unauthenticated users to POST (register), but require auth to GET the list
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        # Security Check: Only admins can view the full list of all users
        if not is_admin(request.user):
            return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        users = list(User.objects.all().values('id', 'username', 'email', 'role', 'email_verified'))
        return Response(users, status=status.HTTP_200_OK)

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role', 'user')

        if not all([username, email, password]):
            return Response({'error': 'username, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, email=email, password=password, role=role)
            return Response({'id': user.id, 'username': user.username, 'role': user.role}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # Helper method to verify users only access their own profile
    def get_object(self, pk, request_user):
        try:
            target_user = User.objects.get(pk=pk)
            # Security Check: User can only access their own profile, unless they are admin
            if target_user != request_user and not is_admin(request_user):
                return None
            return target_user
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk, request.user)
        if not user:
            return Response({'error': 'User not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': user.id, 
            'username': user.username, 
            'email': user.email, 
            'role': user.role, 
            'email_verified': user.email_verified,
            'department': user.department.name if user.department else None,
            'campus': user.campus,
            'phone_number': user.phone_number,
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = self.get_object(pk, request.user)
        if not user:
            return Response({'error': 'User not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        user.username = request.data.get('username', user.username)
        user.email = request.data.get('email', user.email)
        user.email_verified = request.data.get('email_verified', user.email_verified)
        user.department = request.data.get('department', user.department)
        user.campus = request.data.get('campus', user.campus)
        user.phone_number = request.data.get('phone_number', user.phone_number)

        # Only admins can change a user's role
        if is_admin(request.user) and 'role' in request.data:
            user.role = request.data.get('role', user.role)
        
        if 'password' in request.data:
            user.set_password(request.data['password'])

        try:
            user.save()
            return Response({'id': user.id, 'username': user.username, 'role': user.role}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk, request.user)
        if not user:
            return Response({'error': 'User not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            user.delete()
            return Response({'message': 'User deleted successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Cannot delete user: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 5. COMPLAINT RESPONSE VIEWS
# ==========================================

class ComplaintResponseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Admins see all responses
        if is_admin(request.user):
            queryset = ComplaintResponse.objects.all()
        else:
            # Regular users only see non-internal responses for their own complaints
            queryset = ComplaintResponse.objects.filter(
                complaint__user=request.user, 
                is_internal=False
            )

        responses = []
        for r in queryset:
            responses.append({
                'id': r.id,
                'complaint_no': r.complaint.complaint_no,
                'responder': r.responder.username,
                'remarks': r.remarks,
                'is_internal': r.is_internal,
                'created_at': r.created_at.isoformat()
            })
        return Response(responses, status=status.HTTP_200_OK)

    def post(self, request):
        complaint_id = request.data.get('complaint_id')
        remarks = request.data.get('remarks')
        is_internal = request.data.get('is_internal', False)

        if not all([complaint_id, remarks]):
            return Response({'error': 'complaint_id and remarks are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            complaint = Complaint.objects.get(pk=complaint_id)
            
            # Security Check: Prevent users from replying to other people's complaints
            if complaint.user != request.user and not is_admin(request.user):
                return Response({'error': 'Access denied to this complaint.'}, status=status.HTTP_403_FORBIDDEN)

            # Security Check: Only admins can post internal remarks
            if is_internal and not is_admin(request.user):
                is_internal = False
            
            response_obj = ComplaintResponse.objects.create(
                complaint=complaint,
                responder=request.user,
                remarks=remarks,
                is_internal=is_internal
            )
            return Response({
                'id': response_obj.id,
                'complaint_no': complaint.complaint_no,
                'responder': request.user.username
            }, status=status.HTTP_201_CREATED)
            
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ComplaintResponseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            res_obj = ComplaintResponse.objects.get(pk=pk)
            # Admin can view all. Users can view if it's their complaint AND it's not internal.
            if is_admin(user):
                return res_obj
            if res_obj.complaint.user == user and not res_obj.is_internal:
                return res_obj
            return None
        except ComplaintResponse.DoesNotExist:
            return None

    def get(self, request, pk):
        r = self.get_object(pk, request.user)
        if not r:
            return Response({'error': 'Response record not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': r.id,
            'complaint_no': r.complaint.complaint_no,
            'responder': r.responder.username,
            'remarks': r.remarks,
            'is_internal': r.is_internal,
            'created_at': r.created_at.isoformat()
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        r = self.get_object(pk, request.user)
        if not r:
            return Response({'error': 'Response record not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Security Check: Users should only be able to edit their own responses
        if r.responder != request.user and not is_admin(request.user):
             return Response({'error': 'You can only edit your own responses.'}, status=status.HTTP_403_FORBIDDEN)

        r.remarks = request.data.get('remarks', r.remarks)
        
        # Only admins can toggle internal status
        if is_admin(request.user):
            r.is_internal = request.data.get('is_internal', r.is_internal)

        try:
            r.save()
            return Response({'id': r.id, 'remarks': r.remarks, 'is_internal': r.is_internal}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        r = self.get_object(pk, request.user)
        if not r:
            return Response({'error': 'Response record not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
            
        if r.responder != request.user and not is_admin(request.user):
             return Response({'error': 'You can only delete your own responses.'}, status=status.HTTP_403_FORBIDDEN)

        r.delete()
        return Response({'message': 'Response record deleted successfully.'}, status=status.HTTP_200_OK)

# ==========================================
# 4. COMPLAINT STATUS HISTORY VIEWS
# ==========================================
class ComplaintStatusHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_admin(request.user):
            queryset = ComplaintStatusHistory.objects.all()
        else:
            # Users can only see status history for their own complaints
            queryset = ComplaintStatusHistory.objects.filter(complaint__user=request.user)
            
        history = []
        for h in queryset:
            history.append({
                'id': h.id,
                'complaint_no': h.complaint.complaint_no,
                'changed_by': h.changed_by.username,
                'old_status': h.old_status,
                'new_status': h.new_status,
                'note': h.note,
                'created_at': h.created_at.isoformat()
            })
        return Response(history, status=status.HTTP_200_OK)

    def post(self, request):
        complaint_id = request.data.get('complaint_id')
        old_status = request.data.get('old_status')
        new_status = request.data.get('new_status')
        note = request.data.get('note', '')

        if not all([complaint_id, old_status, new_status]):
            return Response({'error': 'complaint_id, old_status, and new_status are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            complaint = Complaint.objects.get(pk=complaint_id)
            
            # Security Check: Only admins or the owner can change the status
            if complaint.user != request.user and not is_admin(request.user):
                 return Response({'error': 'Access denied to this complaint.'}, status=status.HTTP_403_FORBIDDEN)
            
            history_obj = ComplaintStatusHistory.objects.create(
                complaint=complaint,
                changed_by=request.user,
                old_status=old_status,
                new_status=new_status,
                note=note
            )
            
            # Optionally update the actual complaint status as well
            complaint.status = new_status
            complaint.save()
            
            return Response({
                'id': history_obj.id,
                'complaint_no': complaint.complaint_no,
                'status_change': f"{old_status} -> {new_status}"
            }, status=status.HTTP_201_CREATED)
            
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ComplaintStatusHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            h = ComplaintStatusHistory.objects.get(pk=pk)
            if h.complaint.user != user and not is_admin(user):
                return None
            return h
        except ComplaintStatusHistory.DoesNotExist:
            return None

    def get(self, request, pk):
        h = self.get_object(pk, request.user)
        if not h:
            return Response({'error': 'Status history log not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': h.id,
            'complaint_no': h.complaint.complaint_no,
            'changed_by': h.changed_by.username,
            'old_status': h.old_status,
            'new_status': h.new_status,
            'note': h.note,
            'created_at': h.created_at.isoformat()
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        h = self.get_object(pk, request.user)
        if not h:
            return Response({'error': 'Status history log not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Security Check: Generally, history logs shouldn't be edited. If allowed, restrict to admins.
        if not is_admin(request.user):
            return Response({'error': 'Only administrators can edit status history logs.'}, status=status.HTTP_403_FORBIDDEN)

        h.old_status = request.data.get('old_status', h.old_status)
        h.new_status = request.data.get('new_status', h.new_status)
        h.note = request.data.get('note', h.note)
        
        try:
            h.save()
            return Response({
                'id': h.id,
                'complaint_no': h.complaint.complaint_no,
                'status_change': f"{h.old_status} -> {h.new_status}",
                'note': h.note
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        h = self.get_object(pk, request.user)
        if not h:
            return Response({'error': 'Status history log not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Security Check: Only administrators can delete history logs
        if not is_admin(request.user):
            return Response({'error': 'Only administrators can delete status history logs.'}, status=status.HTTP_403_FORBIDDEN)

        h.delete()
        return Response({'message': 'Status history log deleted successfully.'}, status=status.HTTP_200_OK)
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            h = ComplaintStatusHistory.objects.get(pk=pk)
            return Response({
                'id': h.id,
                'complaint_no': h.complaint.complaint_no,
                'changed_by': h.changed_by.username,
                'old_status': h.old_status,
                'new_status': h.new_status,
                'note': h.note,
                'created_at': h.created_at.isoformat()
            })
        except ComplaintStatusHistory.DoesNotExist:
            return Response({'error': 'Status history log not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            history_obj = ComplaintStatusHistory.objects.get(pk=pk)
        except ComplaintStatusHistory.DoesNotExist:
            return Response({'error': 'Status history log not found.'}, status=status.HTTP_404_NOT_FOUND)

        history_obj.old_status = request.data.get('old_status', history_obj.old_status)
        history_obj.new_status = request.data.get('new_status', history_obj.new_status)
        history_obj.note = request.data.get('note', history_obj.note)
        
        try:
            history_obj.save()
            return Response({
                'id': history_obj.id,
                'complaint_no': history_obj.complaint.complaint_no,
                'status_change': f"{history_obj.old_status} -> {history_obj.new_status}",
                'note': history_obj.note
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk):
        try:
            history_obj = ComplaintStatusHistory.objects.get(pk=pk)
            history_obj.delete()
            return Response({'message': 'Status history log deleted successfully.'}, status=status.HTTP_200_OK)
        except ComplaintStatusHistory.DoesNotExist:
            return Response({'error': 'Status history log not found.'}, status=status.HTTP_404_NOT_FOUND)