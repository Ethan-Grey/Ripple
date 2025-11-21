const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const toggleBtn = document.getElementById('sidebarToggle');
        const COLLISION_BREAKPOINT = 1200;
        
        const isSmallWindow = () => window.innerWidth <= COLLISION_BREAKPOINT;
        
        function updateSidebarState() {
            const small = isSmallWindow();
            
            if (small) {
                const isOpen = sidebar.classList.contains('open');
                if (isOpen) {
                    overlay.classList.add('active');
                    document.body.style.overflow = 'hidden';
                } else {
                    overlay.classList.remove('active');
                    document.body.style.overflow = '';
                }
                toggleBtn.classList.remove('shifted');
            } else {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
                toggleBtn.classList.add('shifted');
            }
        }
        
        function toggleSidebar() {
            const small = isSmallWindow();
            
            if (small) {
                const isOpen = sidebar.classList.contains('open');
                if (isOpen) {
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                    document.body.style.overflow = '';
                } else {
                    sidebar.classList.add('open');
                    overlay.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
            }
        }
        
        function closeSidebar() {
            if (isSmallWindow()) {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
        
        // Event listeners
        toggleBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', closeSidebar);
        
        // Close sidebar when clicking nav links on small windows
        const navLinks = sidebar.querySelectorAll('.nav-item');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (isSmallWindow()) {
                    closeSidebar();
                }
            });
        });
        
        // Update on window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                const wasSmall = sidebar.classList.contains('open');
                const isNowSmall = isSmallWindow();
                
                if (!wasSmall && isNowSmall) {
                    sidebar.classList.remove('open');
                }
                
                updateSidebarState();
            }, 100);
        });
        
        // Highlight active nav item based on current path
        const currentPath = window.location.pathname;
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href');
            if (linkPath && currentPath === linkPath) {
                link.classList.add('active');
            } else if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) {
                // Check if this is the longest matching path to avoid conflicts
                const allLinks = Array.from(navLinks);
                const longerMatch = allLinks.some(otherLink => {
                    const otherPath = otherLink.getAttribute('href');
                    return otherPath && 
                           otherPath !== linkPath && 
                           otherPath.startsWith(linkPath) && 
                           currentPath.startsWith(otherPath);
                });
                
                if (!longerMatch) {
                    link.classList.add('active');
                }
            }
        });
        
        // Initialize state
        updateSidebarState();
        
        // Dark mode toggle
        const html = document.documentElement;
        
        // Load saved theme or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-theme', savedTheme);
        
        // Update theme toggle in dropdown
        function updateThemeToggle() {
            const currentTheme = html.getAttribute('data-theme');
            const themeIcon = document.getElementById('themeIcon');
            const themeText = document.getElementById('themeText');
            if (themeIcon && themeText) {
                if (currentTheme === 'dark') {
                    themeIcon.className = 'bi bi-sun me-2';
                    themeText.textContent = 'Light Mode';
                } else {
                    themeIcon.className = 'bi bi-moon me-2';
                    themeText.textContent = 'Dark Mode';
                }
            }
        }
        
        // Initialize theme toggle display
        updateThemeToggle();
        
        // Theme toggle in dropdown
        const themeToggleDropdown = document.getElementById('themeToggleDropdown');
        if (themeToggleDropdown) {
            themeToggleDropdown.addEventListener('click', function(e) {
                e.preventDefault();
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeToggle();
            });
        }