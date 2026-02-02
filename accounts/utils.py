import logging
import requests
import dns.resolver
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger('accounts')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    remote_addr = request.META.get('REMOTE_ADDR')
    
    # 只在开发环境下记录详细的 IP 信息
    if settings.DEBUG:
        logger.debug(f"Client IP resolution: XFF={x_forwarded_for}, XRI={x_real_ip}, RA={remote_addr}")
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = x_real_ip or remote_addr
    
    return ip


def verify_recaptcha(token: str, user_info: dict = None) -> bool:
    """验证 reCAPTCHA token

    Args:
        token: reCAPTCHA token
        user_info: 可选的用户信息字典，用于日志记录（例如：{'email': 'user@example.com', 'ip': '1.2.3.4'}）

    Returns:
        bool: 验证是否通过
    """
    try:
        # 向 Google 验证服务器发送请求
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': token
        })

        # 检查响应状态码
        if response.status_code != 200:
            logger.error(f"reCAPTCHA request failed with status code: {response.status_code}")
            return False

        result = response.json()

        # 提取关键信息用于分析
        success = result.get('success', False)
        score = float(result.get('score', 0))
        action = result.get('action', 'unknown')
        challenge_ts = result.get('challenge_ts', 'unknown')
        hostname = result.get('hostname', 'unknown')
        error_codes = result.get('error-codes', [])

        # 构建日志信息
        log_context = f"score={score}, action={action}, hostname={hostname}"
        if user_info:
            if 'email' in user_info:
                log_context += f", email={user_info['email']}"
            if 'ip' in user_info:
                log_context += f", ip={user_info['ip']}"

        if not success:
            logger.error(f"reCAPTCHA validation failed: {log_context}, errors={error_codes}")
            return False

        # 记录详细的验证结果（用于后续分析）
        threshold = float(settings.RECAPTCHA_SCORE_THRESHOLD)
        logger.info(f"reCAPTCHA verification: {log_context}, threshold={threshold}, challenge_ts={challenge_ts}")

        # 判断是否通过阈值
        if score < threshold:
            logger.warning(f"reCAPTCHA score below threshold: {log_context}, REJECTED")
            return False

        logger.info(f"reCAPTCHA verification PASSED: {log_context}")
        return True

    except requests.RequestException as e:
        logger.error(f"reCAPTCHA network error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"reCAPTCHA unexpected error: {str(e)}")
        return False

def verify_email_domain(email: str) -> bool:
    """验证邮箱域名是否有效"""
    if '@' not in email or email.count('@') != 1:
        logger.warning(f"Invalid email format: {email}")
        return False

    try:
        # 获取域名部分
        domain = email.split('@')[1]
        
        # 添加详细日志
        logger.info(f"Verifying domain: {domain}")
        
        # 查询域名的 MX 记录
        mx_records = dns.resolver.resolve(domain, 'MX')
        
        # 记录找到的 MX 记录
        logger.info(f"Found MX records for {domain}: {[str(r.exchange) for r in mx_records]}")
        
        # 确保至少有一个 MX 记录
        if not list(mx_records):
            logger.warning(f"No MX records found for {domain}")
            return False
            
        return True
        
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers) as e:
        # 只记录日志，不返回具体错误信息
        logger.warning(f"Invalid email domain for {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"DNS query failed for {email}: {str(e)}")
        return False

def check_ip_registration_limit(ip_address: str) -> bool:
    """
    检查IP地址的注册频率
    :param ip_address: IP地址
    :return: True 如果未超过限制，False 如果已超过限制
    """
    limit = settings.IP_RATE_LIMIT_MAX  # 从 settings 中获取最大注册次数
    timeout = settings.IP_RATE_LIMIT_TIMEOUT  # 从 settings 中获取超时时间（秒）
    hours = timeout / 3600  # 将超时时间转换为小时

    try:
        cache_key = f'ip_register_{ip_address}'
        registration_times = cache.get(cache_key, [])
        
        # 清理过期的记录
        now = datetime.now()
        time_window = now - timedelta(hours=hours)
        registration_times = [t for t in registration_times if t > time_window]
        
        # 检查是否超过限制
        if len(registration_times) >= limit:
            logger.warning(f"IP {ip_address} has exceeded registration limit")
            return False
            
        # 添加新的注册时间
        registration_times.append(now)
        cache.set(cache_key, registration_times, timeout=timeout)  # 使用秒作为超时时间
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking IP registration limit: {str(e)}")
        return True  # 如果出错，允许注册以避免影响正常用户
    
