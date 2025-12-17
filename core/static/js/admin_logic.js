document.addEventListener("DOMContentLoaded", function() {
    
    function setupTopNavButton() {
        // 1. Encontra o primeiro link do menu superior (O placeholder "Navegação")
        // Seletor: Primeira lista (.navbar-nav), primeiro item (.nav-item), primeiro link (.nav-link)
        const navButton = document.querySelector('.navbar-nav .nav-item .nav-link');
        
        if (!navButton) return;

        // 2. Lógica de URL
        const currentPath = window.location.pathname;
        const adminRoot = '/admin/';
        const portalRoot = '/'; 

        // Verifica onde estamos
        // Se for EXATAMENTE '/admin/' -> Botão deve levar para o Site
        // Se for qualquer outra coisa (ex: '/admin/core_rh/funcionario/') -> Botão deve levar para o Dashboard
        const isDashboard = (currentPath === adminRoot || currentPath === adminRoot + 'index.html');

        if (isDashboard) {
            // Estamos no Dashboard -> Link para o Site
            navButton.innerHTML = '<i class="fas fa-arrow-left mr-2"></i> Voltar ao Portal';
            navButton.href = portalRoot;
            navButton.title = "Sair da administração";
        } else {
            // Estamos em uma tela interna -> Link para o Dashboard
            navButton.innerHTML = '<i class="fas fa-tachometer-alt mr-2"></i> Dashboard';
            navButton.href = adminRoot;
            navButton.title = "Voltar ao painel principal";
        }
        
        // 3. Estilo Visual (Para destacar o botão)
        navButton.style.fontWeight = "bold";
        navButton.style.color = "#ffffff";
        navButton.style.backgroundColor = "rgba(255, 255, 255, 0.2)"; // Fundo levemente transparente
        navButton.style.borderRadius = "4px";
        navButton.style.padding = "8px 15px";
        navButton.style.marginRight = "10px";
        navButton.style.transition = "background-color 0.3s";

        // Efeito Hover simples via JS
        navButton.onmouseover = function() { this.style.backgroundColor = "rgba(255, 255, 255, 0.3)"; };
        navButton.onmouseout = function() { this.style.backgroundColor = "rgba(255, 255, 255, 0.2)"; };
    }
    /* core/static/js/admin_logic.js */

// --- 2. LIMPEZA DO MENU DE USUÁRIO (NOVA FUNÇÃO) ---
    function cleanUserMenu() {
        // Encontra todos os itens dentro do menu dropdown do usuário
        const menuItems = document.querySelectorAll('.navbar-nav .dropdown-menu .dropdown-item, .navbar-nav .dropdown-menu .dropdown-header');
        
        menuItems.forEach(item => {
            const text = item.innerText.trim().toLowerCase();
            const href = item.getAttribute('href') || '';

            // Se o texto for "Account" ou "See Profile", ou o link apontar para edição de usuário
            if (
                text.includes('account') || 
                text.includes('see profile') || 
                text.includes('perfil') ||
                (href.includes('/user/') && href.includes('/change/'))
            ) {
                item.style.display = 'none';
                item.style.setProperty('display', 'none', 'important');
            }
        });

        // Remove divisórias extras (linhas <div class="dropdown-divider">)
        const dividers = document.querySelectorAll('.navbar-nav .dropdown-menu .dropdown-divider');
        // Mantém apenas a última divisória (antes do Sair), esconde as outras
        dividers.forEach((div, index) => {
            if (index < dividers.length - 1) {
                div.style.display = 'none';
            }
        });
    }
    // Executa
    cleanUserMenu();
    setupTopNavButton();

    // Garante layout limpo
    document.body.style.overflowX = 'hidden';
});