"""
Google My Business Reviews Service
获取并处理Google评论数据
"""

import requests
import logging
from datetime import datetime
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GoogleReviewsService:
    """Google My Business评论服务"""

    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        self.place_id = getattr(settings, 'GOOGLE_PLACE_ID', None)
        self.cache_timeout = 3600  # 1小时缓存

    def get_reviews(self, max_reviews=6, min_rating=None, show_multilingual=False):
        """
        获取Google评论

        Args:
            max_reviews (int): 最大评论数量
            min_rating (int): 最小评分过滤 (1-5), None表示不过滤
            show_multilingual (bool): 是否获取多语言评论

        Returns:
            dict: 包含评论数据和评分信息
        """
        if not self.api_key or not self.place_id:
            logger.warning("Google Places API key or Place ID not configured")
            return None

        # 检查缓存
        cache_key = f'google_reviews_{self.place_id}_{max_reviews}_{min_rating}_{show_multilingual}'
        cached_reviews = cache.get(cache_key)
        if cached_reviews:
            return cached_reviews

        try:
            if show_multilingual:
                # 获取多语言评论
                api_data = self._get_multilingual_reviews()
            else:
                # 获取默认语言评论
                api_data = self._get_default_reviews()

            if api_data is None:
                return None

            result = api_data['result']
            all_reviews = self._process_reviews(result.get('reviews', []))
            filtered_reviews = self._filter_reviews(all_reviews, min_rating, max_reviews)

            reviews_data = {
                'reviews': filtered_reviews,
                'rating': result.get('rating', 0),
                'total_ratings': result.get('user_ratings_total', 0),
                'business_name': result.get('name', 'Appliances 4 Less Doraville'),
                'filtered_count': len(filtered_reviews),
                'total_fetched': len(all_reviews),
                'min_rating_filter': min_rating
            }

            # 缓存结果
            cache.set(cache_key, reviews_data, self.cache_timeout)

            logger.info(f"Successfully fetched {len(reviews_data['reviews'])} Google reviews")
            return reviews_data

        except requests.RequestException as e:
            logger.error(f"Network error when fetching Google reviews: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error when fetching Google reviews: {e}")
            return None

    def _process_reviews(self, raw_reviews):
        """
        处理原始评论数据

        Args:
            raw_reviews (list): 原始评论数据

        Returns:
            list: 处理后的评论数据
        """
        processed_reviews = []

        for review in raw_reviews:
            try:
                # 处理评论时间
                review_time = datetime.fromtimestamp(review.get('time', 0))

                # 处理头像URL
                profile_photo_url = None
                if 'profile_photo_url' in review:
                    profile_photo_url = review['profile_photo_url']

                processed_review = {
                    'author_name': review.get('author_name', 'Anonymous'),
                    'author_url': review.get('author_url', ''),
                    'profile_photo_url': profile_photo_url,
                    'rating': review.get('rating', 0),
                    'text': review.get('text', ''),
                    'time': review_time,
                    'relative_time_description': review.get('relative_time_description', '')
                }

                processed_reviews.append(processed_review)

            except Exception as e:
                logger.warning(f"Error processing review: {e}")
                continue

        return processed_reviews

    def _filter_reviews(self, reviews, min_rating=None, max_count=6):
        """
        过滤评论

        Args:
            reviews (list): 原始评论列表
            min_rating (int): 最小评分过滤
            max_count (int): 最大返回数量

        Returns:
            list: 过滤后的评论列表
        """
        filtered_reviews = reviews

        # 按评分过滤
        if min_rating is not None:
            filtered_reviews = [review for review in filtered_reviews
                              if review.get('rating', 0) >= min_rating]

        # 按时间排序（最新的在前）
        filtered_reviews.sort(key=lambda x: x.get('time', datetime.min), reverse=True)

        # 限制数量
        return filtered_reviews[:max_count]

    def _get_default_reviews(self):
        """获取默认语言评论"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': self.place_id,
            'fields': 'reviews,rating,user_ratings_total,name',
            'key': self.api_key
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['status'] == 'OK' and 'result' in data:
            return data
        else:
            logger.error(f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            return None

    def _get_multilingual_reviews(self):
        """获取英语和西班牙语评论"""
        all_reviews = []
        business_info = None

        # 获取英语和西班牙语评论
        languages = [None, 'es']  # None=默认语言(通常是英语), 'es'=西班牙语

        for language in languages:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': self.place_id,
                'fields': 'reviews,rating,user_ratings_total,name',
                'key': self.api_key
            }

            # 只为西班牙语添加语言参数
            if language:
                params['language'] = language

            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                if data['status'] == 'OK' and 'result' in data:
                    result = data['result']
                    reviews = result.get('reviews', [])

                    # 保存商家信息（只需要一次）
                    if business_info is None:
                        business_info = {
                            'rating': result.get('rating', 0),
                            'user_ratings_total': result.get('user_ratings_total', 0),
                            'name': result.get('name', 'Appliances 4 Less Doraville')
                        }

                    all_reviews.extend(reviews)

            except Exception as e:
                logger.warning(f"Error fetching {language or 'default'} reviews: {e}")
                continue

        if not all_reviews or business_info is None:
            # 如果获取失败，回退到默认方式
            return self._get_default_reviews()

        # 去重（基于作者名称和评论文本前50个字符）
        unique_reviews = []
        seen_reviews = set()

        for review in all_reviews:
            review_key = (review.get('author_name', ''), review.get('text', '')[:50])
            if review_key not in seen_reviews:
                seen_reviews.add(review_key)
                unique_reviews.append(review)

        # 构造返回格式
        return {
            'status': 'OK',
            'result': {
                'reviews': unique_reviews,
                'rating': business_info['rating'],
                'user_ratings_total': business_info['user_ratings_total'],
                'name': business_info['name']
            }
        }

