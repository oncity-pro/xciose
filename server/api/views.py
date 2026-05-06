from django.shortcuts import render
from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Sample, WaterBrand, Customer, BucketDepositConfig, DeliveryRecord
from .serializers import SampleSerializer, WaterBrandSerializer, CustomerSerializer, BucketDepositConfigSerializer, DeliveryRecordSerializer
from .authentication import BearerTokenAuthentication


# ==================== Authentication Views ====================

class LoginView(APIView):
    """
    用户登录视图
    POST /api/auth/login/
    """
    permission_classes = []  # 允许未认证用户访问
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'code': 1,
                'message': '请提供用户名和密码'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # 生成或获取 token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'code': 0,
                'message': '登录成功',
                'data': {
                    'accessToken': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'code': 1,
                'message': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    用户登出视图
    POST /api/auth/logout/
    """
    def post(self, request):
        # 删除用户的 token
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({
                'code': 0,
                'message': '退出成功'
            }, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({
                'code': 0,
                'message': '已退出'
            }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    刷新 Token 视图
    POST /api/auth/refresh/
    """
    def post(self, request):
        # 简单实现：返回当前 token
        try:
            token = Token.objects.get(user=request.user)
            return Response({
                'code': 0,
                'data': token.key
            }, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({
                'code': 1,
                'message': '未授权'
            }, status=status.HTTP_401_UNAUTHORIZED)


class AccessCodesView(APIView):
    """
    获取用户权限码视图
    GET /api/auth/codes/
    """
    def get(self, request):
        # 简单实现：返回所有权限码
        # 实际项目中应该根据用户角色返回对应的权限码
        return Response({
            'code': 0,
            'data': [
                'AC_100100',
                'AC_100110',
                'AC_100120',
                'AC_100010',
                'AC_100020',
                'AC_100030',
            ]
        }, status=status.HTTP_200_OK)


class UserInfoView(APIView):
    """
    获取用户信息视图
    GET /api/user/info/
    """
    def get(self, request):
        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return Response({
                'code': 1,
                'message': '未授权访问'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        
        return Response({
            'code': 0,
            'data': {
                'userId': user.id,
                'username': user.username,
                'realName': f'{user.first_name} {user.last_name}'.strip() or user.username,
                'email': user.email,
                'avatar': None,  # 可以后续添加头像功能
                'desc': None,
                'homePath': '/dashboard',  # 默认首页
                'roles': ['admin'] if user.is_superuser else ['user'],
                'authBtnList': ['*']  # 所有权限
            }
        }, status=status.HTTP_200_OK)


# ==================== Sample Views (原有代码) ====================

class HealthCheckView(APIView):
    """
    健康检查视图
    """
    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'ONCITY API is running'
        }, status=status.HTTP_200_OK)


class SampleListCreateView(generics.ListCreateAPIView):
    """
    示例列表和创建视图
    """
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class SampleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    示例详情、更新和删除视图
    """
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


# ==================== WaterBrand Views ====================

class WaterBrandListView(generics.ListAPIView):
    """
    水品牌列表视图
    """
    queryset = WaterBrand.objects.filter(is_active=True)
    serializer_class = WaterBrandSerializer


class WaterBrandListCreateView(generics.ListCreateAPIView):
    """
    水品牌列表和创建视图
    """
    serializer_class = WaterBrandSerializer
    pagination_class = None  # 禁用分页，返回完整列表

    def get_queryset(self):
        queryset = WaterBrand.objects.all()
        brand_type = self.request.query_params.get('brand_type', None)
        if brand_type:
            queryset = queryset.filter(brand_type=brand_type)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        重写 list 方法，返回 Vben Admin 期望的格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        重写 create 方法，返回 Vben Admin 期望的格式
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class WaterBrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    水品牌详情、更新和删除视图
    """
    queryset = WaterBrand.objects.all()
    serializer_class = WaterBrandSerializer
    
    def update(self, request, *args, **kwargs):
        """
        重写 update 方法，返回 Vben Admin 期望的格式
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        重写 destroy 方法，返回 Vben Admin 期望的格式
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 0,
            'message': '删除成功',
            'data': None
        }, status=status.HTTP_200_OK)


# ==================== Customer Views ====================

class CustomerListView(generics.ListAPIView):
    """
    客户列表视图（支持搜索）
    """
    serializer_class = CustomerSerializer
    
    def get_queryset(self):
        queryset = Customer.objects.all()

        # 获取搜索参数
        keyword = self.request.query_params.get('keyword', None)
        customer_id = self.request.query_params.get('customer_id', None)
        name = self.request.query_params.get('name', None)

        if keyword:
            # 支持按客户编号或姓名模糊搜索（兼容旧逻辑）
            from django.db.models import Q
            queryset = queryset.filter(
                Q(id__icontains=keyword) |
                Q(name__icontains=keyword)
            )
        else:
            if customer_id:
                queryset = queryset.filter(id__icontains=customer_id)
            if name:
                queryset = queryset.filter(name__icontains=name)

        return queryset


class CustomerListCreateView(generics.ListCreateAPIView):
    """
    客户列表和创建视图
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    pagination_class = None  # 禁用分页，返回完整列表

    def get_queryset(self):
        queryset = Customer.objects.all()

        # 获取搜索参数
        keyword = self.request.query_params.get('keyword', None)
        customer_id = self.request.query_params.get('customer_id', None)
        name = self.request.query_params.get('name', None)

        if keyword:
            # 支持按客户编号或姓名模糊搜索（兼容旧逻辑）
            from django.db.models import Q
            queryset = queryset.filter(
                Q(id__icontains=keyword) |
                Q(name__icontains=keyword)
            )
        else:
            if customer_id:
                queryset = queryset.filter(id__icontains=customer_id)
            if name:
                queryset = queryset.filter(name__icontains=name)

        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        重写 list 方法，返回 Vben Admin 期望的格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        重写 create 方法，返回 Vben Admin 期望的格式
        """
        # 添加调试信息
        print(f"收到创建客户的请求数据: {request.data}")
        
        # 检查是否为JSON请求
        content_type = request.content_type if hasattr(request, 'content_type') else request.META.get('CONTENT_TYPE', '')
        print(f"请求内容类型: {content_type}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"数据验证失败: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 双重检查：防止并发导致重复编号
        customer_id = serializer.validated_data.get('id')
        if customer_id and Customer.objects.filter(id=customer_id).exists():
            return Response(
                {'id': ['客户编号已存在，请重新输入']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {'id': ['客户编号已存在，请重新输入']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"客户创建成功: {serializer.data}")
        return Response({
            'code': 0,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class CustomerStatsView(APIView):
    """
    客户统计视图（全局统计，不受搜索参数影响）
    GET /api/v1/customers/stats
    """
    
    def get(self, request):
        from django.db.models import Q
        from django.utils import timezone
        
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # 计算上月
        if current_month == 1:
            last_month = 12
            last_month_year = current_year - 1
        else:
            last_month = current_month - 1
            last_month_year = current_year
        
        # 客户总数
        total = Customer.objects.count()
        
        # 各类型客户数
        vip_count = Customer.objects.filter(customer_type='vip').count()
        normal_count = Customer.objects.filter(customer_type='normal').count()
        pickup_count = Customer.objects.filter(customer_type='pickup').count()
        
        # 本月新增（按开户日期）
        new_this_month = Customer.objects.filter(
            open_date__year=current_year,
            open_date__month=current_month
        ).count()
        
        # 上月新增
        last_month_new = Customer.objects.filter(
            open_date__year=last_month_year,
            open_date__month=last_month
        ).count()
        
        # 本月注销
        closed_this_month = Customer.objects.filter(
            close_date__year=current_year,
            close_date__month=current_month
        ).count()
        
        # 上月注销
        last_month_closed = Customer.objects.filter(
            close_date__year=last_month_year,
            close_date__month=last_month
        ).count()
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'total': total,
                'vipCount': vip_count,
                'normalCount': normal_count,
                'pickupCount': pickup_count,
                'newThisMonth': new_this_month,
                'lastMonthNew': last_month_new,
                'closedThisMonth': closed_this_month,
                'lastMonthClosed': last_month_closed,
            }
        })


class NextCustomerIdView(APIView):
    """
    获取下一个可用客户编号
    GET /api/v1/customers/next-id
    """
    def get(self, request):
        from .models import generate_customer_id
        next_id = generate_customer_id()
        return Response({
            'code': 0,
            'message': 'success',
            'data': {'nextId': next_id}
        })


class CheckCustomerIdView(APIView):
    """
    检查客户编号是否已存在
    GET /api/v1/customers/check-id?id=xxx
    """
    def get(self, request):
        customer_id = request.query_params.get('id', '').strip()
        if not customer_id:
            return Response({
                'code': 0,
                'message': 'success',
                'data': {'exists': False}
            })

        # 精确匹配
        exists = Customer.objects.filter(id=customer_id).exists()

        # 纯数字编号检查数值等价（如 1 与 0001 视为重复）
        if not exists and customer_id.isdigit():
            from django.db import connection
            cast_type = 'INTEGER' if connection.vendor == 'sqlite' else 'UNSIGNED'
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT 1 FROM api_customer WHERE CAST(id AS {cast_type}) = %s LIMIT 1",
                    [int(customer_id)]
                )
                exists = cursor.fetchone() is not None

        return Response({
            'code': 0,
            'message': 'success',
            'data': {'exists': exists}
        })


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    客户详情、更新和删除视图
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        重写 retrieve 方法，返回 Vben Admin 期望的格式
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """
        重写 update 方法，返回 Vben Admin 期望的格式
        默认启用 partial=True，支持前端只传部分字段进行更新
        """
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        # 开户存水量永久不可变更
        data = request.data.copy()
        data.pop('storage_amount', None)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        
        if not serializer.is_valid():
            print(f"数据验证失败: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)
        print(f"客户更新成功: {serializer.data}")
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        重写 destroy 方法，返回 Vben Admin 期望的格式
        """
        instance = self.get_object()
        print(f"准备删除客户: {instance.id} - {instance.name}")
        try:
            self.perform_destroy(instance)
            print(f"客户删除成功: {instance.id}")
            return Response({
                'code': 0,
                'message': '删除成功',
                'data': None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"删除客户失败: {instance.id}, 错误: {str(e)}")
            return Response({
                'code': 1,
                'message': f'删除失败: {str(e)}',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


# ==================== Menu Views ====================

class MenuView(APIView):
    """
    获取用户菜单视图
    GET /api/menu/all/
    
    返回 Vben Admin 期望的路由格式
    """
    def get(self, request):
        # 检查用户是否已认证
        if not request.user or not request.user.is_authenticated:
            return Response({
                'code': 1,
                'message': '未授权访问'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 返回示例菜单结构
        # 实际项目中应该根据用户角色从数据库动态加载菜单
        menus = [
            {
                "name": "Dashboard",
                "path": "/dashboard",
                "component": "BasicLayout",
                "meta": {
                    "title": "仪表盘",
                    "icon": "lucide:layout-dashboard",
                    "order": -1
                },
                "children": [
                    {
                        "name": "Analytics",
                        "path": "/dashboard/analytics",
                        "component": "/dashboard/analytics/index",
                        "meta": {
                            "title": "分析页",
                            "icon": "lucide:area-chart"
                        }
                    },
                    {
                        "name": "Workspace",
                        "path": "/dashboard/workspace",
                        "component": "/dashboard/workspace/index",
                        "meta": {
                            "title": "工作台",
                            "icon": "lucide:briefcase"
                        }
                    }
                ]
            },
            {
                "name": "WaterBrand",
                "path": "/water-brand",
                "component": "BasicLayout",
                "meta": {
                    "title": "水品牌管理",
                    "icon": "lucide:droplet",
                    "order": 1
                },
                "children": [
                    {
                        "name": "WaterBrandList",
                        "path": "/water-brand/list",
                        "component": "/water-brand/list/index",
                        "meta": {
                            "title": "品牌列表",
                            "icon": "lucide:list"
                        }
                    }
                ]
            },
            {
                "name": "Customer",
                "path": "/customer",
                "component": "/customer/index",
                "meta": {
                    "title": "客户管理",
                    "icon": "lucide:users",
                    "order": 2
                }
            },
            {
                "name": "DeliveryOrder",
                "path": "/delivery-order",
                "component": "/delivery-order/index",
                "meta": {
                    "title": "商品出单",
                    "icon": "lucide:clipboard-list",
                    "order": 3
                }
            },
            {
                "name": "DeliveryStats",
                "path": "/delivery-stats",
                "component": "/delivery-stats/index",
                "meta": {
                    "title": "送水统计",
                    "icon": "lucide:bar-chart-3",
                    "order": 4
                }
            }
        ]
        
        return Response({
            'code': 0,
            'data': menus
        }, status=status.HTTP_200_OK)


# ==================== Delivery Record Views ====================

class DeliveryRecordStatsView(APIView):
    """
    按日期汇总各品牌送水量统计视图
    GET /api/v1/delivery-records/stats?date=2026-05-06
    """
    def get(self, request):
        from django.db.models import Sum, F
        from django.db.models.functions import Coalesce

        date_str = request.query_params.get('date', None)
        if not date_str:
            return Response({
                'code': 1,
                'message': '请提供日期参数 date，格式：YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'code': 1,
                'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 查询指定日期的送水记录，按品牌分组汇总
        stats = DeliveryRecord.objects.filter(
            date=target_date,
            customer__brand__isnull=False
        ).values(
            brand_id=F('customer__brand'),
            brand_name=F('customer__brand__name')
        ).annotate(
            total_delivered=Coalesce(Sum('water_delivered'), 0)
        ).order_by('brand_name')

        # 汇总无品牌客户的送水量
        no_brand_total = DeliveryRecord.objects.filter(
            date=target_date,
            customer__brand__isnull=True
        ).aggregate(
            total=Coalesce(Sum('water_delivered'), 0)
        )['total'] or 0

        # 计算总计
        grand_total = sum(item['total_delivered'] for item in stats) + no_brand_total

        result = list(stats)
        if no_brand_total > 0:
            result.append({
                'brand_id': None,
                'brand_name': '未分配品牌',
                'total_delivered': no_brand_total
            })

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'date': date_str,
                'brands': result,
                'total': grand_total
            }
        })


class DeliveryRecordListView(generics.ListAPIView):
    """
    送水记录列表视图
    GET /api/v1/customers/<customer_id>/delivery-records/
    """
    serializer_class = DeliveryRecordSerializer
    pagination_class = None

    def get_queryset(self):
        customer_id = self.kwargs.get('customer_id')
        return DeliveryRecord.objects.filter(customer_id=customer_id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })


class DeliveryRecordCreateView(APIView):
    """
    创建送水记录视图（商品出单）
    POST /api/v1/delivery-records/
    """
    def post(self, request):
        data = request.data
        customer_id = data.get('customer')
        
        if not customer_id:
            return Response({
                'code': 1,
                'message': '客户编号不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({
                'code': 1,
                'message': '客户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DeliveryRecordSerializer(data=data)
        if serializer.is_valid():
            record = serializer.save()
            
            # 更新客户相关字段
            water_delivered = data.get('water_delivered', 0)
            buckets_returned = data.get('buckets_returned', 0)
            
            # 更新总用水量
            customer.total_water_usage = (customer.total_water_usage or 0) + water_delivered
            
            # 注意：不再自动更新客户欠空桶，欠空桶只在编辑客户时修改
            
            # 更新最后送水日期
            from django.utils import timezone
            customer.last_delivery_date = data.get('date') or timezone.now().date()
            
            # 注意：不再自动更新客户存水量，存水量只在编辑客户时修改
            
            # 续存记录：累加消费总额（以 vip_scheme 存在为判断依据）
            vip_scheme = data.get('vip_scheme')
            if vip_scheme and customer.brand and customer.brand.price_per_bucket:
                try:
                    from decimal import Decimal
                    buy_count = int(vip_scheme.split('_')[0])
                    renewal_amount = Decimal(str(buy_count)) * Decimal(str(customer.brand.price_per_bucket))
                    current_total = customer.total_consumption or Decimal('0')
                    # 若消费总额为0且是VIP，先补算开户金额
                    if current_total == 0 and customer.customer_type == 'vip' and customer.vip_scheme:
                        opening_buy = int(customer.vip_scheme.split('_')[0])
                        current_total = Decimal(str(opening_buy)) * Decimal(str(customer.brand.price_per_bucket))
                    customer.total_consumption = current_total + renewal_amount
                except (ValueError, IndexError):
                    pass
            
            customer.save()
            
            return Response({
                'code': 0,
                'message': '出单成功',
                'data': DeliveryRecordSerializer(record).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'code': 1,
            'message': '数据验证失败',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeliveryRecordUpdateView(APIView):
    """
    更新送水记录视图
    PUT /api/v1/delivery-records/<pk>/
    """
    def put(self, request, pk):
        try:
            record = DeliveryRecord.objects.get(pk=pk)
        except DeliveryRecord.DoesNotExist:
            return Response({
                'code': 1,
                'message': '记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 保存旧值用于计算差值
        old_water = record.water_delivered or 0
        old_buckets = record.buckets_returned or 0
        old_storage = record.storage_amount or 0
        old_date = record.date
        
        serializer = DeliveryRecordSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            updated_record = serializer.save()
            
            # 更新客户累计数据
            customer = record.customer
            new_water = updated_record.water_delivered or 0
            new_buckets = updated_record.buckets_returned or 0
            new_storage = updated_record.storage_amount or 0
            
            delta_water = new_water - old_water
            delta_buckets = new_buckets - old_buckets
            
            if delta_water != 0:
                customer.total_water_usage = (customer.total_water_usage or 0) + delta_water
            
            # 注意：不再自动更新客户欠空桶，欠空桶只在编辑客户时修改
            
            # 注意：不再自动更新客户存水量，存水量只在编辑客户时修改
            
            # 如果日期发生变化，更新最后送水日期为最新记录的日期
            if updated_record.date != old_date:
                latest_record = DeliveryRecord.objects.filter(customer=customer).order_by('-date', '-id').first()
                if latest_record:
                    customer.last_delivery_date = latest_record.date
            
            customer.save()
            
            return Response({
                'code': 0,
                'message': '更新成功',
                'data': DeliveryRecordSerializer(updated_record).data
            })
        
        return Response({
            'code': 1,
            'message': '数据验证失败',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeliveryRecordDeleteView(APIView):
    """
    删除送水记录视图
    DELETE /api/v1/delivery-records/<pk>/
    """
    def delete(self, request, pk):
        try:
            record = DeliveryRecord.objects.get(pk=pk)
        except DeliveryRecord.DoesNotExist:
            return Response({
                'code': 1,
                'message': '记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        customer = record.customer
        water_delivered = record.water_delivered or 0
        buckets_returned = record.buckets_returned or 0
        
        # 回滚客户累计数据
        customer.total_water_usage = (customer.total_water_usage or 0) - water_delivered
        
        # 注意：不再自动回滚客户欠空桶，欠空桶只在编辑客户时修改
        # 注意：续存记录删除时不回滚客户存水量，客户信息（新建时的数据）永久不变
        
        # 删除记录
        record.delete()
        
        # 更新最后送水日期为最新记录的日期
        latest_record = DeliveryRecord.objects.filter(customer=customer).order_by('-date', '-id').first()
        if latest_record:
            customer.last_delivery_date = latest_record.date
            # 注意：不再自动更新客户存水量，存水量只在编辑客户时修改
        else:
            customer.last_delivery_date = None
            # 注意：不再自动重置客户存水量
        
        customer.save()
        
        return Response({
            'code': 0,
            'message': '删除成功',
            'data': None
        }, status=status.HTTP_200_OK)


# ==================== Bucket Deposit Config Views ====================

class BucketDepositConfigView(APIView):
    """
    空桶押金配置视图
    GET  /api/v1/bucket-deposit-config/  获取配置
    PUT  /api/v1/bucket-deposit-config/  更新配置
    """
    def get(self, request):
        config, created = BucketDepositConfig.objects.get_or_create(
            id=1,
            defaults={'amount_per_bucket': 30.00}
        )
        serializer = BucketDepositConfigSerializer(config)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })

    def put(self, request):
        config, created = BucketDepositConfig.objects.get_or_create(
            id=1,
            defaults={'amount_per_bucket': 30.00}
        )
        serializer = BucketDepositConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 0,
                'message': '更新成功',
                'data': serializer.data
            })
        return Response({
            'code': 1,
            'message': '数据验证失败',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
