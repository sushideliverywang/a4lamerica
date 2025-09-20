// 工具函数
const utils = {
    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// 全局函数
function showLogoutModal() {
    const modal = document.getElementById('logoutModal');
    if (modal) {
        modal.classList.remove('hidden');
        // 同时隐藏用户菜单
        const userMenu = document.getElementById('userMenu');
        const mobileUserMenu = document.getElementById('mobileUserMenu');
        if (userMenu) userMenu.classList.add('hidden');
        if (mobileUserMenu) mobileUserMenu.classList.add('hidden');
    }
}

function hideLogoutModal() {
    const modal = document.getElementById('logoutModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// UI组件
const components = {
    // 轮播图组件
    carousel: {
        init(container) {
            const wrapper = container.querySelector('.carousel-wrapper');
            const items = container.querySelectorAll('.carousel-item');
            let currentIndex = 0;
            let startX = 0;
            let isDragging = false;

            // 更新轮播图位置
            function updateSlide() {
                wrapper.style.transform = `translateX(-${currentIndex * 100}%)`;
            }

            // 显示下一张
            function nextSlide() {
                currentIndex = (currentIndex + 1) % items.length;
                updateSlide();
            }

            // 显示上一张
            function prevSlide() {
                currentIndex = (currentIndex - 1 + items.length) % items.length;
                updateSlide();
            }

            // 触摸事件处理
            wrapper.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
                isDragging = true;
            });

            wrapper.addEventListener('touchmove', (e) => {
                if (!isDragging) return;
                const currentX = e.touches[0].clientX;
                const diff = startX - currentX;
                
                wrapper.style.transform = `translateX(calc(-${currentIndex * 100}% - ${diff}px))`;
            });

            wrapper.addEventListener('touchend', (e) => {
                if (!isDragging) return;
                const endX = e.changedTouches[0].clientX;
                const diff = startX - endX;
                
                if (Math.abs(diff) > 50) {
                    if (diff > 0) {
                        nextSlide();
                    } else {
                        prevSlide();
                    }
                } else {
                    updateSlide();
                }
                
                isDragging = false;
            });

            // 鼠标事件处理
            wrapper.addEventListener('mousedown', (e) => {
                startX = e.clientX;
                isDragging = true;
            });

            wrapper.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                const currentX = e.clientX;
                const diff = startX - currentX;
                
                wrapper.style.transform = `translateX(calc(-${currentIndex * 100}% - ${diff}px))`;
            });

            wrapper.addEventListener('mouseup', (e) => {
                if (!isDragging) return;
                const endX = e.clientX;
                const diff = startX - endX;
                
                if (Math.abs(diff) > 50) {
                    if (diff > 0) {
                        nextSlide();
                    } else {
                        prevSlide();
                    }
                } else {
                    updateSlide();
                }
                
                isDragging = false;
            });

            wrapper.addEventListener('mouseleave', () => {
                if (isDragging) {
                    updateSlide();
                    isDragging = false;
                }
            });

            // 自动轮播
            setInterval(nextSlide, 5000);

            // 绑定按钮事件
            const prevButton = container.querySelector('.carousel-button.prev');
            const nextButton = container.querySelector('.carousel-button.next');
            
            if (prevButton) prevButton.addEventListener('click', prevSlide);
            if (nextButton) nextButton.addEventListener('click', nextSlide);
        }
    },

    // 产品展示组件
    productDisplay: {
        init(container) {
            // 产品展示组件已简化，不再需要滚动按钮功能
            // 因为home页面每行正好显示6个产品，无需滚动
        }
    }
};

// 页面功能
const pages = {
    // 首页特定功能
    home: {
        init() {
            // 初始化店铺轮播
            const storeCarousel = document.querySelector('.carousel-container');
            if (storeCarousel) {
                components.carousel.init(storeCarousel);
            }

            // 初始化产品展示
            document.querySelectorAll('.product-scroll-container').forEach(container => {
                components.productDisplay.init(container);
            });
        }
    },

    // 商店页面特定功能
    store: {
        init() {
            // 初始化产品展示
            document.querySelectorAll('.product-scroll-container').forEach(container => {
                components.productDisplay.init(container);
            });
        }
    }
};

// 事件处理
const events = {
    // 用户菜单
    initUserMenu() {
        const menu = document.getElementById('userMenu');
        const button = document.getElementById('userMenuButton');
        
        if (menu && button) {
            button.addEventListener('click', () => {
                menu.classList.toggle('hidden');
            });

            document.addEventListener('click', (event) => {
                if (!menu.contains(event.target) && !button.contains(event.target)) {
                    menu.classList.add('hidden');
                }
            });
        }
    },

    // 登出模态框
    initLogoutModal() {
        const modal = document.getElementById('logoutModal');
        
        if (modal) {
            // 点击模态框外部关闭
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    hideLogoutModal();
                }
            });

            // ESC 键关闭模态框
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
                    hideLogoutModal();
                }
            });
        }
    },

    // 桌面端 Shop All 菜单
    initShopAllMenu() {
        const shopAllButton = document.querySelector('.navbar .group button');
        const shopAllMenu = document.querySelector('.navbar .group > div');
        
        if (shopAllButton && shopAllMenu) {
            // 点击按钮显示/隐藏菜单
            shopAllButton.addEventListener('click', (e) => {
                e.preventDefault();
                shopAllMenu.classList.toggle('hidden');
            });

            // 点击外部区域隐藏菜单
            document.addEventListener('click', (event) => {
                if (!shopAllMenu.contains(event.target) && !shopAllButton.contains(event.target)) {
                    shopAllMenu.classList.add('hidden');
                }
            });
        }
    }
};

// 设备检测
const isMobile = window.innerWidth <= 767;

// 初始化函数
function initializeComponents() {
    if (isMobile) {
        initializeMobileComponents();
    } else {
        initializeDesktopComponents();
    }
}

// 移动端组件初始化
function initializeMobileComponents() {
    // 移动端特定功能
    const mobileMenu = document.getElementById('mobileCategoryMenu');
    const mobileUserMenu = document.getElementById('mobileUserMenu');
    const mobileShopAllButton = document.getElementById('mobileShopAllButton');
    const mobileUserMenuButton = document.getElementById('mobileUserMenuButton');
    
    // 移动端菜单处理
    if (mobileMenu && mobileShopAllButton) {
        // 点击 Shop All 按钮显示/隐藏菜单
        mobileShopAllButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

        // 点击遮罩层关闭菜单
        const overlay = mobileMenu.querySelector('.absolute.inset-0');
        if (overlay) {
            overlay.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
            });
        }
    }
    
    // 移动端用户菜单处理
    if (mobileUserMenu && mobileUserMenuButton) {
        // 点击用户菜单按钮显示/隐藏菜单
        mobileUserMenuButton.addEventListener('click', () => {
            mobileUserMenu.classList.toggle('hidden');
        });

        // 点击遮罩层关闭菜单
        mobileUserMenu.addEventListener('click', (e) => {
            if (e.target === mobileUserMenu) {
                mobileUserMenu.classList.add('hidden');
            }
        });

        // 点击关闭按钮关闭菜单
        const closeButton = mobileUserMenu.querySelector('button');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                mobileUserMenu.classList.add('hidden');
            });
        }
    }
}

// 桌面端组件初始化
function initializeDesktopComponents() {
    // 桌面端特定功能
    const desktopMenu = document.querySelector('.navbar .group > div');
    const userMenu = document.getElementById('userMenu');
    
    // 桌面端菜单处理
    if (desktopMenu) {
        // 桌面端菜单相关代码
    }
    
    if (userMenu) {
        // 桌面端用户菜单相关代码
    }
}

// 监听窗口大小变化
window.addEventListener('resize', () => {
    const newIsMobile = window.innerWidth <= 767;
    if (newIsMobile !== isMobile) {
        // 设备类型改变时重新初始化
        initializeComponents();
    }
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化页面特定功能
    if (document.body.classList.contains('home-page')) {
        pages.home.init();
    } else if (document.body.classList.contains('store-page')) {
        pages.store.init();
    }

    // 初始化通用事件
    events.initUserMenu();
    events.initLogoutModal();
    events.initShopAllMenu();

    // 初始化移动端组件
    initializeMobileComponents();
}); 