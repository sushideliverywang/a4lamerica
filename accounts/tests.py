# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Customer
from .forms import CustomerRegistrationForm

class CustomerRegistrationTest(TestCase):
    """客户注册功能测试"""
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register_customer')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'phone': '1234567890',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register_page_loads(self):
        """测试注册页面是否正常加载"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register_customer.html')

    def test_valid_registration(self):
        """测试有效数据的注册流程"""
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, 302)  # 重定向状态码
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Customer.objects.count(), 1)

    def test_invalid_registration(self):
        """测试无效数据的注册流程"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid_email'
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_duplicate_username(self):
        """测试重复用户名注册"""
        User.objects.create_user(username='testuser', email='existing@example.com', password='TestPass123!')
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue('username' in response.context['form'].errors)

    def test_duplicate_email(self):
        """测试重复邮箱注册"""
        User.objects.create_user(username='existing', email='test@example.com', password='TestPass123!')
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue('email' in response.context['form'].errors)