const { useState, useEffect } = React;

function api(path, opts = {}){
  const base = '/api';
  const token = localStorage.getItem('speckit.token');
  const headers = opts.headers || {};
  if(token) headers['Authorization'] = 'Bearer ' + token;
  return fetch(base + path, Object.assign({}, opts, { headers })).then(async res => {
    const json = await res.json().catch(()=>null);
    if(!res.ok) throw json || { error: 'Request failed' };
    return json;
  });
}

function AuthForm({onLogin}){
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const [error,setError]=useState('');

  async function handleRegister(e){
    e.preventDefault(); setError('');
    try{
      await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}).then(r=>r.json());
      // auto login
      const j = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}).then(r=>r.json());
      localStorage.setItem('speckit.token', j.token);
      onLogin(j.username);
    }catch(err){ setError(err && err.error ? err.error : 'Failed'); }
  }

  async function handleLogin(e){
    e.preventDefault(); setError('');
    try{
      const j = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}).then(r=>r.json());
      localStorage.setItem('speckit.token', j.token);
      onLogin(j.username);
    }catch(err){ setError(err && err.error ? err.error : 'Failed'); }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-semibold mb-4">Sign in or Register</h2>
      <form className="space-y-3" onSubmit={handleLogin}>
        <div>
          <label className="block text-sm text-gray-600">Username</label>
          <input className="mt-1 w-full border rounded p-2" value={username} onChange={e=>setUsername(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm text-gray-600">Password</label>
          <input type="password" className="mt-1 w-full border rounded p-2" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        {error && <div className="text-red-600">{error}</div>}
        <div className="flex gap-2">
          <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={handleLogin}>Sign in</button>
          <button className="bg-gray-100 px-4 py-2 rounded" onClick={handleRegister}>Register</button>
        </div>
      </form>
    </div>
  );
}

function Dashboard({username, onLogout}){
  const [college, setCollege] = useState('');
  const [degree, setDegree] = useState('');
  const [skills, setSkills] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function validate(){
    setError('');
    if(!file) { setError('Please select a PDF resume.'); return false }
    if(!file.name.toLowerCase().endsWith('.pdf')) { setError('Only PDF files are accepted.'); return false }
    return true;
  }

  async function handleSubmit(e){
    e.preventDefault(); setResult(null);
    if(!validate()) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('resume', file);
    fd.append('college', college);
    fd.append('degree', degree);
    fd.append('skills', skills);
    try{
      const res = await fetch('/api/compare', { method: 'POST', headers: { 'Authorization': 'Bearer ' + localStorage.getItem('speckit.token') }, body: fd }).then(r=>r.json());
      if(res.error) throw res;
      setResult(res);
    }catch(err){ setError(err && err.error ? err.error : 'Failed to compare'); }
    setLoading(false);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <div>
          <span className="text-sm text-gray-600 mr-4">{username}</span>
          <button className="text-sm text-red-600" onClick={()=>{ localStorage.removeItem('speckit.token'); onLogout(); }}>Sign out</button>
        </div>
      </div>

      <form className="bg-white p-4 rounded shadow space-y-3" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm text-gray-600">College Name</label>
          <input className="mt-1 w-full border rounded p-2" value={college} onChange={e=>setCollege(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm text-gray-600">Degree</label>
          <input className="mt-1 w-full border rounded p-2" value={degree} onChange={e=>setDegree(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm text-gray-600">Skills (comma separated)</label>
          <input className="mt-1 w-full border rounded p-2" value={skills} onChange={e=>setSkills(e.target.value)} placeholder="e.g. JavaScript, React, Node.js" />
        </div>
        <div>
          <label className="block text-sm text-gray-600">Resume PDF</label>
          <input className="mt-1" type="file" accept="application/pdf" onChange={e=>setFile(e.target.files[0] || null)} />
        </div>
        {error && <div className="text-red-600">{error}</div>}
        <div>
          <button className="bg-green-600 text-white px-4 py-2 rounded" disabled={loading}>{loading ? 'Processing...' : 'Compare Resume'}</button>
        </div>
      </form>

      {result && (
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-semibold mb-2">Results</h3>
          <table className="w-full table-auto text-sm">
            <tbody>
              <tr className="border-t"><td className="py-2 font-medium">Match Percentage</td><td className="py-2">{result.matchPercentage}%</td></tr>
              <tr className="border-t"><td className="py-2 font-medium">Skill Match %</td><td className="py-2">{result.skillMatchPercent}%</td></tr>
              <tr className="border-t"><td className="py-2 font-medium">Matching Skills</td><td className="py-2">{result.matchingSkills.length ? result.matchingSkills.join(', ') : '—'}</td></tr>
              <tr className="border-t"><td className="py-2 font-medium">Missing Skills</td><td className="py-2">{result.missingSkills.length ? result.missingSkills.join(', ') : '—'}</td></tr>
              <tr className="border-t"><td className="py-2 font-medium">Education Match</td><td className="py-2">{result.collegeMatch ? 'Yes' : 'No'}</td></tr>
              <tr className="border-t"><td className="py-2 font-medium">Degree Match</td><td className="py-2">{result.degreeMatch ? 'Yes' : 'No'}</td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App(){
  const [user, setUser] = useState(null);

  useEffect(()=>{
    const token = localStorage.getItem('speckit.token');
    if(!token) return;
    api('/whoami').then(j=>setUser(j.username)).catch(()=>localStorage.removeItem('speckit.token'));
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Speckit — Resume Comparison</h1>
      {!user ? <AuthForm onLogin={(u)=>setUser(u)} /> : <Dashboard username={user} onLogout={()=>setUser(null)} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
