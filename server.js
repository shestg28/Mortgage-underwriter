const express = require('express');
const multer = require('multer');
const pdf = require('pdf-parse');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 3000;

// In-memory stores
const users = new Map(); // username -> { username, password }
const sessions = new Map(); // token -> username

function makeToken(){ return Math.random().toString(36).slice(2) + Date.now().toString(36) }

// Serve static frontend
app.use(express.static(path.join(__dirname, 'public')));

// Multer setup
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: (req, file, cb) => {
    if(file.mimetype !== 'application/pdf' && !file.originalname.toLowerCase().endsWith('.pdf')){
      return cb(new Error('Only PDF allowed'))
    }
    cb(null, true)
  }
});

app.post('/api/register', (req, res) => {
  const { username, password } = req.body || {};
  if(!username || !password) return res.status(400).json({ error: 'Missing username or password' });
  if(users.has(username)) return res.status(400).json({ error: 'User already exists' });
  users.set(username, { username, password });
  return res.json({ ok: true });
});

app.post('/api/login', (req, res) => {
  const { username, password } = req.body || {};
  if(!username || !password) return res.status(400).json({ error: 'Missing username or password' });
  const u = users.get(username);
  if(!u || u.password !== password) return res.status(401).json({ error: 'Invalid credentials' });
  const token = makeToken();
  sessions.set(token, username);
  return res.json({ token, username });
});

function authMiddleware(req, res, next){
  const auth = req.headers.authorization || '';
  const parts = auth.split(' ');
  if(parts.length !== 2 || parts[0] !== 'Bearer') return res.status(401).json({ error: 'Unauthorized' });
  const token = parts[1];
  const username = sessions.get(token);
  if(!username) return res.status(401).json({ error: 'Invalid session' });
  req.username = username;
  next();
}

app.post('/api/compare', authMiddleware, upload.single('resume'), async (req, res) => {
  try{
    const { college = '', degree = '', skills = '' } = req.body || {};
    if(!req.file) return res.status(400).json({ error: 'Missing resume file' });

    const dataBuffer = req.file.buffer;
    const parsed = await pdf(dataBuffer);
    const text = (parsed.text || '').toLowerCase();

    const wantedSkills = (skills || '').split(',').map(s=>s.trim()).filter(Boolean);
    const matchingSkills = [];
    const missingSkills = [];
    for(const s of wantedSkills){
      const token = s.toLowerCase();
      const found = text.includes(token);
      if(found) matchingSkills.push(s);
      else missingSkills.push(s);
    }

    const skillMatchPercent = wantedSkills.length ? Math.round((matchingSkills.length / wantedSkills.length) * 100) : 0;
    const collegeMatch = college ? text.includes(college.toLowerCase()) : false;
    const degreeMatch = degree ? text.includes(degree.toLowerCase()) : false;

    // Combine into an overall score (weights: skills 70%, college 20%, degree 10%)
    const overall = Math.round((skillMatchPercent * 0.7) + (collegeMatch ? 100 * 0.2 : 0) + (degreeMatch ? 100 * 0.1 : 0));

    return res.json({
      matchPercentage: overall,
      skillMatchPercent,
      matchingSkills,
      missingSkills,
      collegeMatch,
      degreeMatch,
      // small snippet for debugging
      snippet: (text || '').slice(0, 800)
    });
  }catch(err){
    console.error(err);
    return res.status(500).json({ error: 'Failed to parse PDF' });
  }
});

app.get('/api/whoami', authMiddleware, (req, res) => {
  res.json({ username: req.username });
});

app.listen(PORT, ()=>{
  console.log('Server running on port', PORT);
});
