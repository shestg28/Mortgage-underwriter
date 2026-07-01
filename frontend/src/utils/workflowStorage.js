const CUSTOMER_KEY = 'speckit_customer_id'
const APPLICATION_KEY = 'speckit_application_id'
const DOCUMENTS_KEY = 'speckit_document_ids'

export function setCustomerId(customerId) {
  localStorage.setItem(CUSTOMER_KEY, customerId)
}

export function getCustomerId() {
  return localStorage.getItem(CUSTOMER_KEY) || ''
}

export function setApplicationId(applicationId) {
  localStorage.setItem(APPLICATION_KEY, applicationId)
}

export function getApplicationId() {
  return localStorage.getItem(APPLICATION_KEY) || ''
}

export function setDocumentIds(documentIds) {
  localStorage.setItem(DOCUMENTS_KEY, JSON.stringify(documentIds || []))
}

export function getDocumentIds() {
  try {
    return JSON.parse(localStorage.getItem(DOCUMENTS_KEY) || '[]')
  } catch {
    return []
  }
}
