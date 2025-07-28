let selectedUserType = 'usuario';
// Toggle para mostrar/ocultar contraseña
document.getElementById('togglePassword').addEventListener('click', function () {
    const passwordInput = document.getElementById('password');
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? '👁️' : '🙈';
});

document.querySelectorAll('.user-type-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.user-type-option').forEach(opt => opt.classList.remove('active'));
        this.classList.add('active');
        selectedUserType = this.dataset.type;
        const usernameInput = document.getElementById('username');
        usernameInput.placeholder = selectedUserType === 'administrador'
            ? 'Ingrese su usuario de administrador'
            : 'Ingrese su nombre de usuario';
    });
});
function showForgotPassword() {
  alert("📞 Por favor, comuníquese con el administrador del sistema para recuperar su contraseña.");
}
async function login() {
  const user = document.getElementById("login-user").value;
  const pass = document.getElementById("login-pass").value;

  const res = await fetch("/api/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ usuario: user, password: pass })
});

  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("usuario", JSON.stringify(data));
    window.location.href = "index.html";
  } else {
    document.getElementById("login-error").innerText = "Credenciales incorrectas";
  }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    successDiv.style.display = 'none';
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => errorDiv.style.display = 'none', 5000);
}

function showSuccess(message) {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    errorDiv.style.display = 'none';
    successDiv.textContent = message;
    successDiv.style.display = 'block';
}

function setLoading(isLoading) {
    const button = document.getElementById('loginButton');
    const loading = document.getElementById('loading');
    const buttonText = document.getElementById('buttonText');
    if (isLoading) {
        button.disabled = true;
        loading.style.display = 'inline-block';
        buttonText.textContent = 'Iniciando sesión...';
    } else {
        button.disabled = false;
        loading.style.display = 'none';
        buttonText.textContent = 'Iniciar Sesión';
    }
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    if (!username) {
        showError('Por favor, ingrese su nombre de usuario.');
        return;
    }
    if (!password) {
        showError('Por favor, ingrese su contraseña.');
        return;
    }
    if (password.length < 4) {
        showError('La contraseña debe tener al menos 4 caracteres.');
        return;
    }

    setLoading(true);

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: username, password: password })
        });
        const result = await res.json();

        if (res.ok && result.success) {
            if (rememberMe) {
                localStorage.setItem('rememberedUser', username);
                localStorage.setItem('rememberedUserType', selectedUserType);
            }
            sessionStorage.setItem('userType', result.rol); // admin o usuario
            sessionStorage.setItem('permisos', JSON.stringify(result.permisos));
            sessionStorage.setItem('isLoggedIn', 'true');
            sessionStorage.setItem('loginTime', new Date().toISOString());

            showSuccess('¡Inicio de sesión exitoso! Redirigiendo...');
            setTimeout(() => window.location.href = 'index.html', 1500);
        } else {
            showError(result.mensaje || 'Usuario o contraseña incorrectos.');
            setLoading(false);
        }
    } catch (error) {
        showError('Error al conectar con el servidor.');
        setLoading(false);
    }
});

// Cargar usuario recordado al cargar la página
window.addEventListener('load', function() {
    const rememberedUser = localStorage.getItem('rememberedUser');
    const rememberedUserType = localStorage.getItem('rememberedUserType');
    if (rememberedUser) {
        document.getElementById('username').value = rememberedUser;
        document.getElementById('rememberMe').checked = true;
        if (rememberedUserType) {
            document.querySelectorAll('.user-type-option').forEach(opt => {
                opt.classList.remove('active');
                if (opt.dataset.type === rememberedUserType) {
                    opt.classList.add('active');
                    selectedUserType = rememberedUserType;
                }
            });
        }
    }
});