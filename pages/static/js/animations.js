
class AnimationController {
    constructor() {
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupParallax();
        this.setupScrollEffects();
        this.setupButtonEffects();
        this.setupLoadingAnimations();
        this.setupFormAnimations();
    }

    // Intersection Observer for scroll animations
    setupIntersectionObserver() {
        const options = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Add stagger animation to children
                    const children = entry.target.querySelectorAll('.stagger-item');
                    children.forEach((child, index) => {
                        setTimeout(() => {
                            child.style.opacity = '1';
                            child.style.transform = 'translateY(0)';
                        }, index * 100);
                    });
                }
            });
        }, options);

        // Observe elements with animation classes
        document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right, .feature-box').forEach(el => {
            observer.observe(el);
        });
    }

    setupParallax() {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.parallax-bg');
            
            parallaxElements.forEach(element => {
                const speed = element.dataset.speed || 0.5;
                const yPos = -(scrolled * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });
        });
    }

    // Scroll-based animations
    setupScrollEffects() {
    
        let lastScrollTop = 0;
        const header = document.querySelector('header');
        
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (header) {
                if (scrollTop > lastScrollTop && scrollTop > 100) {
                    header.style.transform = 'translateY(-100%)';
                } else {
                    header.style.transform = 'translateY(0)';
                }
            }
            
            lastScrollTop = scrollTop;
        });

            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupButtonEffects() {
        
        
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                ripple.classList.add('ripple');
                
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });

        // Add pulse to important CTAs
        document.querySelectorAll('.btn-danger, .btn-primary').forEach(btn => {
            btn.classList.add('pulse');
        });
    }

    // Loading animations
    setupLoadingAnimations() {
        // Page load animation
        window.addEventListener('load', () => {
            document.body.classList.add('loaded');
            
            // Animate elements on load
            const elements = document.querySelectorAll('.text-reveal, .hero-section');
            elements.forEach((el, index) => {
                setTimeout(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, index * 200);
            });
        });

        // Show loading spinner for async operations
        this.showLoadingSpinner = (element) => {
            const spinner = document.createElement('div');
            spinner.className = 'spinner';
            element.appendChild(spinner);
            return spinner;
        };

        this.hideLoadingSpinner = (spinner) => {
            if (spinner) {
                spinner.remove();
            }
        };
    }

    setupFormAnimations() {
        document.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
        });

        window.shakeElement = (element) => {
            element.classList.add('shake');
            setTimeout(() => {
                element.classList.remove('shake');
            }, 500);
        };

        window.bounceElement = (element) => {
            element.classList.add('bounce');
            setTimeout(() => {
                element.classList.remove('bounce');
            }, 1000);
        };
    }

    addFloatingAnimation() {
        document.querySelectorAll('.floating').forEach(el => {
            el.style.animation = 'float 3s ease-in-out infinite';
        });
    }

    addGlowEffect() {
        document.querySelectorAll('.glow').forEach(el => {
            el.addEventListener('mouseenter', function() {
                this.style.boxShadow = '0 0 20px rgba(220, 53, 69, 0.8)';
            });
            
            el.addEventListener('mouseleave', function() {
                this.style.boxShadow = '0 0 5px rgba(220, 53, 69, 0.5)';
            });
        });
    }
    setupCardEffects() {
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    }
    setupCustomCursor() {

        if (window.matchMedia('(hover: none)').matches) {
            return; 
        }


        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        cursor.style.cssText = `
            position: fixed;
            width: 20px;
            height: 20px;
            border: 2px solid #ffb300;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transform: translate(-50%, -50%);
            transition: all 0.1s ease;
            opacity: 0;
            mix-blend-mode: difference;
        `;
        document.body.appendChild(cursor);

        const cursorFollower = document.createElement('div');
        cursorFollower.className = 'cursor-follower';
        cursorFollower.style.cssText = `
            position: fixed;
            width: 40px;
            height: 40px;
            background: rgba(255, 251, 5, 0.13);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9998;
            transform: translate(-50%, -50%);
            transition: all 0.3s ease;
            opacity: 0;
        `;
        document.body.appendChild(cursorFollower);

        // Hide default cursor on body
        document.body.style.cursor = 'none';

        let mouseX = 0, mouseY = 0;
        let cursorX = 0, cursorY = 0;
        let followerX = 0, followerY = 0;
        let isHovering = false;

        // Mouse move handler
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            // Show cursors
            cursor.style.opacity = '1';
            cursorFollower.style.opacity = '1';
        });

        // Smooth animation loop
        const animateCursor = () => {
            // Main cursor follows mouse directly
            cursorX += (mouseX - cursorX) * 0.5;
            cursorY += (mouseY - cursorY) * 0.5;
            cursor.style.left = cursorX + 'px';
            cursor.style.top = cursorY + 'px';

            // Follower has delay
            followerX += (mouseX - followerX) * 0.1;
            followerY += (mouseY - followerY) * 0.1;
            cursorFollower.style.left = followerX + 'px';
            cursorFollower.style.top = followerY + 'px';

            requestAnimationFrame(animateCursor);
        };
        animateCursor();

        // Enhanced hover effects
        const setupHoverEffect = (elements, scale = 1.5, bgColor = 'rgba(220, 53, 69, 0.2)') => {
            elements.forEach(element => {
                element.addEventListener('mouseenter', () => {
                    isHovering = true;
                    cursor.style.transform = `translate(-50%, -50%) scale(${scale})`;
                    cursor.style.background = bgColor;
                    cursor.style.borderColor = '#fff700';
                    cursorFollower.style.transform = `translate(-50%, -50%) scale(${scale})`;
                    cursorFollower.style.background = bgColor.replace('0.2', '0.3');
                });

                element.addEventListener('mouseleave', () => {
                    isHovering = false;
                    cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                    cursor.style.background = 'transparent';
                    cursorFollower.style.transform = 'translate(-50%, -50%) scale(1)';
                    cursorFollower.style.background = 'rgba(220, 53, 69, 0.1)';
                });
            });
        };

        // Different hover effects for different elements
        setupHoverEffect(document.querySelectorAll('a, button, .btn'), 1.5, 'rgba(220, 53, 69, 0.2)');
        setupHoverEffect(document.querySelectorAll('.card'), 1.8, 'rgba(220, 53, 69, 0.15)');
        setupHoverEffect(document.querySelectorAll('input, textarea, select'), 1.3, 'rgba(220, 53, 69, 0.1)');

        // Click effect with ripple
        document.addEventListener('mousedown', (e) => {
            cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
            cursorFollower.style.transform = 'translate(-50%, -50%) scale(0.8)';
            
            // Create click ripple
            const ripple = document.createElement('div');
            ripple.style.cssText = `
                position: fixed;
                width: 10px;
                height: 10px;
                background: rgba(220, 217, 53, 0.72);
                border-radius: 50%;
                pointer-events: none;
                z-index: 9996;
                transform: translate(-50%, -50%);
                left: ${e.clientX}px;
                top: ${e.clientY}px;
                animation: clickRipple 0.6s ease-out forwards;
            `;
            document.body.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });

        document.addEventListener('mouseup', () => {
            cursor.style.transform = isHovering ? 'translate(-50%, -50%) scale(1.5)' : 'translate(-50%, -50%) scale(1)';
            cursorFollower.style.transform = isHovering ? 'translate(-50%, -50%) scale(1.5)' : 'translate(-50%, -50%) scale(1)';
        });

        // Hide cursor when leaving window
        document.addEventListener('mouseleave', () => {
            cursor.style.opacity = '0';
            cursorFollower.style.opacity = '0';
        });

        // Show cursor when entering window
        document.addEventListener('mouseenter', () => {
            cursor.style.opacity = '1';
            cursorFollower.style.opacity = '1';
        });

        // Enhanced cursor trail effect
        const createTrailDot = (x, y) => {
            const dot = document.createElement('div');
            dot.className = 'cursor-trail-dot';
            dot.style.cssText = `
                position: fixed;
                width: 6px;
                height: 6px;
                background: rgb(246, 255, 0);
                border-radius: 50%;
                pointer-events: none;
                z-index: 9997;
                transform: translate(-50%, -50%);
                left: ${x}px;
                top: ${y}px;
                animation: trailFade 1s ease forwards;
            `;
            document.body.appendChild(dot);
            
            setTimeout(() => {
                dot.remove();
            }, 1000);
        };

        // Create trail dots on mouse move (throttled)
        let trailTimer;
        let lastTrailTime = 0;
        document.addEventListener('mousemove', (e) => {
            const currentTime = Date.now();
            if (currentTime - lastTrailTime > 50) {
                clearTimeout(trailTimer);
                trailTimer = setTimeout(() => {
                    createTrailDot(e.clientX, e.clientY);
                }, 10);
                lastTrailTime = currentTime;
            }
        });

        // Add click ripple animation to CSS
        const clickRippleCSS = `
            @keyframes clickRipple {
                to {
                    width: 40px;
                    height: 40px;
                    opacity: 0;
                    transform: translate(-50%, -50%) scale(4);
                }
            }
        `;
        
        const clickStyle = document.createElement('style');
        clickStyle.textContent = clickRippleCSS;
        document.head.appendChild(clickStyle);
    }

    // Initialize all animations
    initializeAll() {
        this.addFloatingAnimation();
        this.addGlowEffect();
        this.setupCardEffects();
        this.setupCustomCursor();
        
        // Add stagger animation to product cards
        document.querySelectorAll('.card').forEach((card, index) => {
            card.classList.add('stagger-item');
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }
}

// Inject ripple CSS before DOM loads
const rippleCSS = `
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s ease-out;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.focused {
    transform: scale(1.02);
    box-shadow: 0 0 0 3px rgba(220, 201, 53, 0.1);
}

.loaded {
    opacity: 1;
}

/* Custom cursor animations */
@keyframes trailFade {
    0% {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }
    100% {
        opacity: 0;
        transform: translate(-50%, -50%) scale(0.3);
    }
}

.cursor-trail-dot {
    pointer-events: none;
}

/* Disable custom cursor on mobile devices */
@media (max-width: 768px) {
    .custom-cursor,
    .cursor-follower,
    .cursor-trail-dot {
        display: none !important;
    }
    
    body {
        cursor: auto !important;
    }
}
`;

const style = document.createElement('style');
style.textContent = rippleCSS;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for all elements to be ready
    setTimeout(() => {
        const animationController = new AnimationController();
        animationController.initializeAll();
        
        // Make it globally available
        window.animations = animationController;
        
        console.log('Animations initialized successfully');
    }, 100);
});
