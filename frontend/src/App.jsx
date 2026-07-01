import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/DashboardLayout'
import DashboardPage from './pages/DashboardPage'
import CustomerRegistrationPage from './pages/CustomerRegistrationPage'
import CustomerSearchPage from './pages/CustomerSearchPage'
import LoanApplicationPage from './pages/LoanApplicationPage'
import DocumentUploadPage from './pages/DocumentUploadPage'
import OCRResultsPage from './pages/OCRResultsPage'
import AnalyzeApplicationPage from './pages/AnalyzeApplicationPage'
import FraudAnalysisPage from './pages/FraudAnalysisPage'
import DecisionResultsPage from './pages/DecisionResultsPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import NotFoundPage from './pages/NotFoundPage'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="customers/register" element={<CustomerRegistrationPage />} />
            <Route path="customers/search" element={<CustomerSearchPage />} />
            <Route path="applications" element={<LoanApplicationPage />} />
            <Route path="upload" element={<DocumentUploadPage />} />
            <Route path="ocr-results" element={<OCRResultsPage />} />
            <Route path="analyze-application" element={<AnalyzeApplicationPage />} />
            <Route path="fraud-analysis" element={<FraudAnalysisPage />} />
            <Route path="decision-results" element={<DecisionResultsPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
