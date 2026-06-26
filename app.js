const MAX_PDF_BYTES = 10 * 1024 * 1024; // 10 MB
const VALID_CREDENTIAL = { username: 'user@example.com', password: 'password123' };

function q(sel){return document.querySelector(sel)}

function showGlobalMessage(text, cls=''){
  const el = q('#global-message');
  el.textContent = text;
  el.className = 'message ' + (cls || '');
}

function sanitizeFileName(name){ return name.replace(/[^a-zA-Z0-9._-]/g,'_').slice(0,200) }

function createLoginSection(){
  const root = q('#login-section');
  root.innerHTML = `
    <form id="login-form" novalidate>
      <label for="username">Username</label>
      <input id="username" name="username" type="text" placeholder="user@example.com" required />

      <label for="password">Password</label>
      <input id="password" name="password" type="password" placeholder="password" required />

      <div class="row">
        <button type="submit">Sign in</button>
        <button type="button" class="secondary" id="forgot">Help</button>
      </div>
      <div id="login-error" class="error" aria-live="polite"></div>
    </form>
  `;

  const form = q('#login-form');
  form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const username = q('#username').value.trim();
    const password = q('#password').value;
    const err = q('#login-error');
    err.textContent = '';

    if(!username || !password){ err.textContent = 'Please enter both username and password.'; return }

    if(username !== VALID_CREDENTIAL.username || password !== VALID_CREDENTIAL.password){
      err.textContent = 'Invalid username or password.';
      showGlobalMessage('Login failed. Check your credentials.', 'error');
      return;
    }

    // success
    localStorage.setItem('speckit.loggedIn','1');
    showGlobalMessage('Signed in successfully.', 'success');
    q('#login-section').classList.add('hidden');
    q('#upload-section').classList.remove('hidden');
  });

  q('#forgot').addEventListener('click', ()=>{
    showGlobalMessage('No backend: use username user@example.com and password password123', '');
  });
}

function createUploadSection(){
  const root = q('#upload-section');
  root.innerHTML = `
    <form id="upload-form">
      <label for="pdf">Upload PDF</label>
      <input id="pdf" name="pdf" type="file" accept="application/pdf" required />

      <div class="row">
        <button type="submit">Upload</button>
        <button type="button" class="secondary" id="signout">Sign out</button>
      </div>
      <div id="upload-error" class="error" aria-live="polite"></div>
      <div id="file-info" class="file-info"></div>
    </form>
  `;

  const form = q('#upload-form');
  form.addEventListener('submit',(e)=>{
    e.preventDefault();
    const fileInput = q('#pdf');
    const err = q('#upload-error');
    const info = q('#file-info');
    err.textContent = '';
    info.textContent = '';

    if(!fileInput.files || fileInput.files.length === 0){ err.textContent = 'Please select a PDF file to upload.'; return }
    const file = fileInput.files[0];

    if(!isPdfFile(file)){
      err.textContent = 'Invalid file. Only PDF files are accepted.'; return
    }
    if(file.size > MAX_PDF_BYTES){
      err.textContent = `File too large. Max ${Math.round(MAX_PDF_BYTES/1024/1024)} MB.`; return
    }

    const safeName = sanitizeFileName(file.name);
    info.textContent = `Ready to upload: ${safeName} — ${Math.round(file.size/1024)} KB`;
    showGlobalMessage('File validated locally. No server in this demo.', 'success');
  });

  q('#signout').addEventListener('click', ()=>{
    localStorage.removeItem('speckit.loggedIn');
    q('#upload-section').classList.add('hidden');
    q('#login-section').classList.remove('hidden');
    showGlobalMessage('Signed out.');
  });
}

function isPdfFile(file){
  if(!file) return false;
  const name = file.name || '';
  const mime = file.type || '';
  return mime === 'application/pdf' || name.toLowerCase().endsWith('.pdf');
}

function init(){
  createLoginSection();
  createUploadSection();
  if(localStorage.getItem('speckit.loggedIn')){
    q('#login-section').classList.add('hidden');
    q('#upload-section').classList.remove('hidden');
  }
}

window.addEventListener('DOMContentLoaded', init);
