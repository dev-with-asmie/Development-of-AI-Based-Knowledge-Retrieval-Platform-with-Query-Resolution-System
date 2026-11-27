
import { useState } from 'react'
import {
  LayoutDashboard, Files, MessageSquare, Search, Activity,
  Settings, Plus, ArrowUpRight, Database, FileText,
  Sparkles, ChevronRight, UploadCloud, CheckCircle2, Zap,
  Menu, X, Send, Loader2, Clock3, Layers3, CircleHelp,
  Server, BrainCircuit, Filter, Copy, Check, Mic, Volume2, VolumeX, Square
} from 'lucide-react'

const API_URL = 'http://127.0.0.1:8001'

const navigation = [
  { name: 'Overview', icon: LayoutDashboard },
  { name: 'Knowledge Base', icon: Files },
  { name: 'Ask Documents', icon: MessageSquare },
  { name: 'Retrieval Explorer', icon: Search },
  { name: 'Evaluation', icon: Activity },
]

const exampleQuestions = [
  'Give me the status of each ticket_id',
  'Which tickets are still open?',
  'Show me all critical priority tickets',
  'What is the status of the laptop battery issue?',
]

// --------------------------------------------------
// RETRIEVAL HELPERS
// --------------------------------------------------

function getResultScore(result) {
  const score =
    result.relevance_score ??
    result.similarity_score ??
    result.score ??
    result.keyword_score

  return typeof score === 'number' ? score : null
}

function getScoreLabel(result) {
  if (typeof result.relevance_score === 'number') return 'Relevance'
  if (typeof result.similarity_score === 'number') return 'Similarity'
  if (typeof result.keyword_score === 'number') return 'Keyword match'
  if (typeof result.score === 'number') return 'Score'
  return 'Score unavailable'
}

function formatScore(score) {
  return score === null ? 'N/A' : score.toFixed(4)
}

function formatHeader(header) {
  return header
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

// Detect and parse structured ticket passages.
// Only ticket-style CSV data is converted into a table.
function parseStructuredTable(text) {
  if (!text || typeof text !== 'string') return null

  const lines = text
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)

  if (lines.length < 2) return null

  const parseRow = line =>
    line.split('|').map(cell => cell.trim())

  const headers = parseRow(lines[0])
  const normalizedHeaders = headers.map(header => header.toLowerCase())

  const requiredColumns = ['ticket_id', 'priority', 'status']

  if (!requiredColumns.every(column =>
    normalizedHeaders.includes(column)
  )) {
    return null
  }

  const rows = lines
    .slice(1)
    .map(parseRow)
    .filter(row => row.length === headers.length)

  if (!rows.length) return null

  return { headers, rows }
}

function getBadgeStyle(type, value) {
  const normalized = String(value || '').toLowerCase()

  if (type === 'priority') {
    if (normalized === 'critical') {
      return 'border-red-500/30 bg-red-500/10 text-red-300'
    }

    if (normalized === 'high') {
      return 'border-orange-500/30 bg-orange-500/10 text-orange-300'
    }

    if (normalized === 'medium') {
      return 'border-amber-500/30 bg-amber-500/10 text-amber-300'
    }

    if (normalized === 'low') {
      return 'border-slate-600 bg-slate-800 text-slate-300'
    }
  }

  if (type === 'status') {
    if (normalized === 'resolved') {
      return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
    }

    if (normalized === 'open') {
      return 'border-amber-500/30 bg-amber-500/10 text-amber-300'
    }

    if (normalized.includes('pending')) {
      return 'border-violet-500/30 bg-violet-500/10 text-violet-300'
    }
  }

  return 'border-slate-700 bg-slate-800 text-slate-300'
}

// --------------------------------------------------
// MAIN APPLICATION
// --------------------------------------------------

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [mobileMenu, setMobileMenu] = useState(false)

  const [question, setQuestion] = useState('')
  const [searching, setSearching] = useState(false)
  const [queryResults, setQueryResults] = useState([])
  const [searchedQuestion, setSearchedQuestion] = useState('')
  const [queryError, setQueryError] = useState('')
  const [queryCount, setQueryCount] = useState(0)
  const [queryHistory, setQueryHistory] = useState([])

  const [generatedAnswer, setGeneratedAnswer] = useState('')
  const [clarificationMessage, setClarificationMessage] = useState('')
  const [generationNotice, setGenerationNotice] = useState('')

  // Persistent ID for normal multi-turn conversation memory.
  const [conversationId, setConversationId] = useState(null)

  // Separate ID for a question currently waiting for clarification.
  const [pendingConversationId, setPendingConversationId] = useState(null)
  const [pendingOriginalQuestion, setPendingOriginalQuestion] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [voiceError, setVoiceError] = useState('')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [answerSources, setAnswerSources] = useState([])
  const [retrievalConfidence, setRetrievalConfidence] = useState(null)

  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadErrors, setUploadErrors] = useState([])
  const [uploadedDocuments, setUploadedDocuments] = useState([])

  const [copiedIndex, setCopiedIndex] = useState(null)

  const totalChunks = uploadedDocuments.reduce(
    (total, doc) => total + (doc.chunks || 0),
    0
  )

  // --------------------------------------------------
  // DOCUMENT UPLOAD AND PROCESSING
  // --------------------------------------------------

  async function handleFilesSelected(event) {
    const files = Array.from(event.target.files || [])

    if (!files.length) return

    setUploading(true)
    setUploadMessage('')
    setUploadErrors([])

    let successCount = 0
    let duplicateCount = 0

    const errors = []

    try {
      for (const file of files) {
        try {
          const formData = new FormData()
          formData.append('file', file)

          const uploadResponse = await fetch(
            `${API_URL}/documents/upload`,
            {
              method: 'POST',
              body: formData,
            }
          )

          const uploadData = await uploadResponse.json()

          if (!uploadResponse.ok) {
            throw new Error(
              uploadData.detail || 'Upload failed'
            )
          }

          const document = uploadData.document

          const storedFilename = document.stored_filename
          const isDuplicate = document.duplicate === true

          const processResponse = await fetch(
            `${API_URL}/documents/${encodeURIComponent(storedFilename)}/process`,
            { method: 'POST' }
          )

          const processData = await processResponse.json()

          if (!processResponse.ok) {
            throw new Error(
              processData.detail || 'Document processing failed'
            )
          }

          const updatedDocument = {
            name: file.name,
            storedFilename,
            chunks: processData.total_chunks || 0,
            vectors: processData.vectors_stored || 0,
            dimensions: processData.embedding_dimensions || 384,
            status: isDuplicate
              ? 'Reused and indexed'
              : 'Indexed',
            duplicate: isDuplicate,
          }

          setUploadedDocuments(previous => [
            updatedDocument,
            ...previous.filter(
              doc => doc.storedFilename !== storedFilename
            ),
          ])

          successCount++

          if (isDuplicate) duplicateCount++

        } catch (error) {
          errors.push(`${file.name}: ${error.message}`)
        }
      }

      let message =
        `${successCount} of ${files.length} document(s) processed successfully.`

      if (duplicateCount > 0) {
        message +=
          ` ${duplicateCount} duplicate file(s) were detected and reused.`
      }

      setUploadMessage(message)
      setUploadErrors(errors)

    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  // --------------------------------------------------
  // DOCUMENT QUERY
  // --------------------------------------------------

  async function handleAskQuestion(event, selectedQuestion = null) {
    event?.preventDefault()

    const currentQuestion = (
      selectedQuestion ?? question
    ).trim()

    if (!currentQuestion || searching) return

    const isClarificationReply = Boolean(pendingConversationId)
    const originalQuestion = isClarificationReply
      ? pendingOriginalQuestion
      : currentQuestion

    setSearching(true)
    setQueryError('')
    setQueryResults([])
    setGeneratedAnswer('')
    setGenerationNotice('')

    if (!isClarificationReply) {
      setClarificationMessage('')
      setSearchedQuestion(currentQuestion)
    }

    try {
      const requestBody = {
        query: originalQuestion,
        top_k: 5,
        // Reuse the same ID for normal follow-up questions.
        conversation_id: isClarificationReply
          ? pendingConversationId
          : conversationId,
      }

      if (isClarificationReply) {
        requestBody.clarification_response = currentQuestion
      }

      const response = await fetch(`${API_URL}/documents/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      const data = await response.json()

      // Keep the backend-issued conversation ID for subsequent turns.
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to process your question.'
        )
      }

      const results = data.retrieval?.results || []
      const responseData = data.response || {}
      const resultStatus = data.status || responseData.status
      setAnswerSources(Array.isArray(responseData.sources) ? responseData.sources : [])
      setRetrievalConfidence(
        data.retrieval?.confidence ??
        data.retrieval?.retrieval_confidence ??
        responseData.retrieval_confidence ?? null
      )

      // After a clarification reply, show the actual refined query used
      // by the backend retrieval pipeline instead of leaving the original
      // vague question (for example, "why?") in the evidence heading.
      if (isClarificationReply) {
        setSearchedQuestion(
          data.refined_query ||
          data.retrieval?.query ||
          `${originalQuestion} ${currentQuestion}`.trim()
        )
      }

      setQueryResults(results)
      setQueryCount(previous => previous + 1)

      const historyLabel = isClarificationReply
        ? `${originalQuestion} → ${currentQuestion}`
        : currentQuestion

      setQueryHistory(previous => [
        {
          question: historyLabel,
          resultCount: results.length,
          time: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        },
        ...previous,
      ].slice(0, 8))

      // Handle expired sessions before checking whether retrieval returned results.
      if (resultStatus === 'clarification_expired') {
        setPendingConversationId(null)
        setPendingOriginalQuestion('')
        setClarificationMessage('')
        setQuestion('')
        setQueryError(
          data.message || responseData.answer ||
          'This clarification session has expired. Please ask your question again.'
        )
      } else if (resultStatus === 'clarification_required') {
        setClarificationMessage(
          data.clarification?.clarification_question ||
          responseData.answer ||
          'Could you provide a little more detail so I can search the right information?'
        )

        if (data.conversation_id) {
          setPendingConversationId(data.conversation_id)
          setPendingOriginalQuestion(originalQuestion)
        } else {
          setQueryError(
            'The server requested clarification but did not return a conversation ID. Please try asking your question again.'
          )
          setPendingConversationId(null)
          setPendingOriginalQuestion('')
        }

        setQuestion('')
      } else if (
        responseData.status === 'generated' &&
        typeof responseData.answer === 'string' &&
        responseData.answer.trim()
      ) {
        setGeneratedAnswer(responseData.answer)
        setClarificationMessage('')
        setPendingConversationId(null)
        setPendingOriginalQuestion('')
        setQuestion('')
      } else if (
        resultStatus === 'generation_failed' ||
        responseData.status === 'generation_failed'
      ) {
        setGenerationNotice(
          responseData.message ||
          'Relevant document passages were retrieved, but the answer-generation service is temporarily unavailable. You can still review the source evidence below.'
        )
        setClarificationMessage('')
        setPendingConversationId(null)
        setPendingOriginalQuestion('')
        setQuestion('')
      } else if (
        resultStatus === 'no_relevant_results' ||
        results.length === 0
      ) {
        setQueryError(
          data.message ||
          responseData.message ||
          'No matching information was found in the indexed documents. Try rephrasing your question or uploading relevant documents.'
        )
        setClarificationMessage('')
        setPendingConversationId(null)
        setPendingOriginalQuestion('')
        setQuestion('')
      } else if (
        typeof responseData.answer === 'string' &&
        responseData.answer.trim()
      ) {
        setGeneratedAnswer(responseData.answer)
        setClarificationMessage('')
        setPendingConversationId(null)
        setPendingOriginalQuestion('')
        setQuestion('')
      } else {
        setQueryError(
          'The server returned an unexpected response. Please try again.'
        )
      }

    } catch (error) {
      setQueryError(
        error.message || 'Something went wrong. Please try again.'
      )

    } finally {
      setSearching(false)
    }
  }

  // --------------------------------------------------
  // M3.3 VOICE INPUT AND TEXT-TO-SPEECH
  // --------------------------------------------------

  function startVoiceInput() {
    setVoiceError('')
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setVoiceError('Voice input is not supported in this browser. Please use Chrome or Edge, or type your question.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onstart = () => setIsListening(true)
    recognition.onresult = event => {
      const transcript = event.results?.[0]?.[0]?.transcript
      if (transcript) setQuestion(previous => previous ? `${previous} ${transcript}` : transcript)
    }
    recognition.onerror = event => {
      setVoiceError(event.error === 'not-allowed'
        ? 'Microphone permission was denied. Allow microphone access in your browser settings.'
        : `Voice input error: ${event.error}. You can type your question instead.`)
    }
    recognition.onend = () => setIsListening(false)
    try {
      recognition.start()
    } catch (error) {
      setIsListening(false)
      setVoiceError(error.message || 'Could not start voice input.')
    }
  }

  function speakAnswer() {
    if (!generatedAnswer || !('speechSynthesis' in window)) {
      setVoiceError('Text-to-speech is not available in this browser.')
      return
    }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(generatedAnswer)
    utterance.lang = 'en-IN'
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utterance)
  }

  function stopSpeaking() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }

  function cancelClarification() {
    setPendingConversationId(null)
    setPendingOriginalQuestion('')
    setClarificationMessage('')
    setQuestion('')
    setQueryError('')
  }

  // --------------------------------------------------
  // COPY RETRIEVED PASSAGE
  // --------------------------------------------------

  async function copyPassage(text, index) {
    try {
      await navigator.clipboard.writeText(text)

      setCopiedIndex(index)

      setTimeout(() => {
        setCopiedIndex(null)
      }, 1500)

    } catch {
      setQueryError('Unable to copy this passage.')
    }
  }

  // --------------------------------------------------
  // NAVIGATION
  // --------------------------------------------------

  function navigateTo(page) {
    setActivePage(page)
    setMobileMenu(false)
  }

  // --------------------------------------------------
  // DASHBOARD DATA
  // --------------------------------------------------

  const stats = [
    {
      label: 'Documents Processed',
      value: uploadedDocuments.length,
      detail: 'This session',
      icon: Files,
      color: 'text-violet-400',
      bg: 'bg-violet-500/10',
    },
    {
      label: 'Knowledge Chunks',
      value: totalChunks,
      detail: 'Processed this session',
      icon: Database,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
    },
    {
      label: 'Queries Executed',
      value: queryCount,
      detail: 'This session',
      icon: Search,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
    },
    {
      label: 'Embedding Dimensions',
      value: '384',
      detail: 'all-MiniLM-L6-v2',
      icon: Zap,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
    },
  ]

  const pageDescriptions = {
    Overview: 'Your intelligent knowledge workspace at a glance.',
    'Knowledge Base': 'Upload, process and manage your knowledge sources.',
    'Ask Documents': 'Ask questions and retrieve relevant information from your documents.',
    'Retrieval Explorer': 'Inspect retrieved passages, source documents and relevance scores.',
    Evaluation: 'Review the retrieval evaluation and testing status.',
  }

  // --------------------------------------------------
  // RESULT CARD
  // --------------------------------------------------

  function renderResultCard(result, index) {
    const score = getResultScore(result)
    const structuredData = parseStructuredTable(result.text || '')

    const getColumnIndex = name =>
      structuredData
        ? structuredData.headers.findIndex(
            header => header.toLowerCase() === name
          )
        : -1

    const ticketIdIndex = getColumnIndex('ticket_id')
    const priorityIndex = getColumnIndex('priority')
    const statusIndex = getColumnIndex('status')

    return (
      <div
        key={`${result.filename}-${result.chunk_index}-${index}`}
        className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 shadow-lg shadow-black/10 transition hover:border-violet-500/30"
      >
        {/* RESULT HEADER */}

        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="rounded-xl border border-violet-500/20 bg-violet-500/10 p-2.5">
              <FileText
                size={19}
                className="text-violet-400"
              />
            </div>

            <div className="min-w-0">
              <p className="break-all text-sm font-semibold text-slate-200">
                {result.filename || 'Unknown document'}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Source document · Chunk {result.chunk_index ?? 'N/A'}
              </p>
            </div>
          </div>

          <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1.5 text-xs font-medium text-violet-300">
            Result {index + 1}
          </span>
        </div>

        {/* RETRIEVED CONTENT */}

        <div className="p-5">
          {structuredData ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h4 className="text-sm font-semibold text-slate-100">
                    Structured ticket records
                  </h4>

                  <p className="mt-1 text-xs text-slate-500">
                    {structuredData.rows.length} record(s) in this passage
                  </p>
                </div>

                <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-300">
                  CSV data
                </span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-700/80">
                <table className="w-full min-w-[850px] border-collapse text-left">
                  <thead className="bg-slate-800/80">
                    <tr>
                      {structuredData.headers.map(header => (
                        <th
                          key={header}
                          className="whitespace-nowrap border-b border-slate-700 px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
                        >
                          {formatHeader(header)}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-800">
                    {structuredData.rows.map((row, rowIndex) => (
                      <tr
                        key={`${row[ticketIdIndex] || 'record'}-${rowIndex}`}
                        className="transition hover:bg-slate-800/40"
                      >
                        {row.map((cell, cellIndex) => {
                          const isTicketId =
                            cellIndex === ticketIdIndex

                          const isPriority =
                            cellIndex === priorityIndex

                          const isStatus =
                            cellIndex === statusIndex

                          return (
                            <td
                              key={`${cellIndex}-${rowIndex}`}
                              className={`max-w-[340px] px-4 py-4 align-top text-sm leading-6 ${
                                isTicketId
                                  ? 'whitespace-nowrap font-semibold text-violet-300'
                                  : 'whitespace-normal break-words text-slate-300'
                              }`}
                            >
                              {isPriority || isStatus ? (
                                <span
                                  className={`inline-flex whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-medium ${getBadgeStyle(
                                    isPriority ? 'priority' : 'status',
                                    cell
                                  )}`}
                                >
                                  {cell}
                                </span>
                              ) : (
                                cell || '—'
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="text-xs text-slate-500">
                Scroll horizontally to view all columns on smaller screens.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <FileText
                  size={15}
                  className="text-cyan-400"
                />

                <h4 className="text-sm font-semibold text-slate-200">
                  Retrieved document passage
                </h4>
              </div>

              <div className="rounded-xl border border-slate-800 bg-[#090d18] p-5">
                <div className="max-h-[500px] overflow-y-auto">
                  <p className="whitespace-pre-wrap break-words text-[13px] leading-7 text-slate-300 [overflow-wrap:anywhere]">
                    {result.text || 'No text available.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* RETRIEVAL METADATA */}

        <div className="border-t border-slate-800 bg-slate-950/40 px-5 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <Layers3
                  size={14}
                  className="text-violet-400"
                />
                Chunk {result.chunk_index ?? 'N/A'}
              </span>

              <span className="flex items-center gap-1.5">
                <Activity
                  size={14}
                  className="text-cyan-400"
                />
                {getScoreLabel(result)}:

                <span className="font-medium tabular-nums text-slate-200">
                  {formatScore(score)}
                </span>
              </span>

              {typeof result.keyword_score === 'number' && (
                <span className="flex items-center gap-1.5">
                  <Search
                    size={13}
                    className="text-cyan-400"
                  />

                  Keyword:

                  <span className="font-medium tabular-nums text-slate-200">
                    {result.keyword_score.toFixed(4)}
                  </span>
                </span>
              )}
            </div>

            <button
              onClick={() => copyPassage(result.text || '', index)}
              className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-400 transition hover:border-violet-500/40 hover:bg-violet-500/10 hover:text-white"
            >
              {copiedIndex === index ? (
                <>
                  <Check
                    size={14}
                    className="text-emerald-400"
                  />
                  Copied
                </>
              ) : (
                <>
                  <Copy size={14} />
                  Copy passage
                </>
              )}
            </button>
          </div>

          {Array.isArray(result.matched_records) &&
            result.matched_records.length > 0 && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
                <CheckCircle2
                  size={15}
                  className="text-emerald-400"
                />

                <p className="text-xs text-emerald-300">
                  {result.matched_records.length} matching structured record(s)
                </p>
              </div>
            )}
        </div>
      </div>
    )
  }

  // --------------------------------------------------
  // PAGE CONTENT
  // --------------------------------------------------

  function renderContent() {

    // ================================================
    // KNOWLEDGE BASE
    // ================================================

    if (activePage === 'Knowledge Base') {
      return (
        <div className="space-y-6">

          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">
                Your documents
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Knowledge sources available in your workspace
              </p>
            </div>

            <label
              className={`flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white ${
                uploading
                  ? 'cursor-not-allowed opacity-50'
                  : 'cursor-pointer hover:bg-violet-500'
              }`}
            >
              <Plus size={17} />

              {uploading ? 'Processing...' : 'Select files'}

              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.csv"
                className="hidden"
                onChange={handleFilesSelected}
                disabled={uploading}
              />
            </label>
          </div>

          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-10 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-500/10">
              <UploadCloud
                className="text-violet-400"
                size={32}
              />
            </div>

            <h3 className="font-medium">
              Upload your knowledge
            </h3>

            <p className="mt-2 text-sm text-slate-400">
              PDF, DOCX, TXT and CSV files supported
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Maximum file size: 20 MB
            </p>

            <label
              className={`mt-5 inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-300 ${
                uploading
                  ? 'cursor-not-allowed opacity-50'
                  : 'cursor-pointer hover:bg-slate-800'
              }`}
            >
              <UploadCloud size={16} />

              {uploading
                ? 'Processing documents...'
                : 'Choose documents'}

              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.csv"
                className="hidden"
                onChange={handleFilesSelected}
                disabled={uploading}
              />
            </label>
          </div>

          {uploading && (
            <div className="flex items-center gap-3 rounded-xl border border-violet-500/30 bg-violet-500/10 p-4">
              <Loader2
                className="animate-spin text-violet-400"
                size={20}
              />

              <div>
                <p className="text-sm font-medium text-violet-300">
                  Processing documents...
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  Extracting text, creating chunks, generating embeddings and indexing in Qdrant.
                </p>
              </div>
            </div>
          )}

          {uploadMessage && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-sm text-emerald-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={17} />
                {uploadMessage}
              </div>
            </div>
          )}

          {uploadErrors.length > 0 && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <p className="mb-2 text-sm font-medium text-red-300">
                Some files could not be processed
              </p>

              {uploadErrors.map((error, index) => (
                <p
                  key={index}
                  className="mt-1 break-words text-xs text-slate-400"
                >
                  {error}
                </p>
              ))}
            </div>
          )}

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold">
                Indexed documents
              </h3>

              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
                {uploadedDocuments.length} this session
              </span>
            </div>

            {uploadedDocuments.length === 0 ? (
              <div className="py-8 text-center">
                <Files
                  className="mx-auto mb-3 text-slate-600"
                  size={30}
                />

                <p className="text-sm text-slate-400">
                  No documents uploaded in this session yet.
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Select a file above to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {uploadedDocuments.map(doc => (
                  <div
                    key={doc.storedFilename}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950 p-4"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="rounded-lg bg-violet-500/10 p-2">
                        <FileText
                          className="text-violet-400"
                          size={19}
                        />
                      </div>

                      <div className="min-w-0">
                        <p className="break-all text-sm font-medium">
                          {doc.name}
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          {doc.chunks} chunks · {doc.vectors} vectors · {doc.dimensions} dimensions
                        </p>
                      </div>
                    </div>

                    <span className="flex items-center gap-1 text-xs text-emerald-400">
                      <CheckCircle2 size={14} />
                      {doc.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="mb-4 font-semibold">
              Supported formats
            </h3>

            <div className="grid gap-3 sm:grid-cols-4">
              {['PDF', 'DOCX', 'TXT', 'CSV'].map(format => (
                <div
                  key={format}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-center"
                >
                  <FileText className="mx-auto mb-2 text-violet-400" />
                  <span className="text-sm">{format}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )
    }

    // ================================================
    // ASK DOCUMENTS
    // ================================================

    if (activePage === 'Ask Documents') {
      return (
        <div className="mx-auto max-w-5xl space-y-6">

          <div className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 via-slate-900 to-cyan-500/5 p-6 sm:p-8">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/15">
              <Sparkles
                className="text-violet-400"
                size={25}
              />
            </div>

            <h2 className="text-xl font-semibold sm:text-2xl">
              Ask your knowledge base
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Ask natural-language questions and let the query-understanding, retrieval,
              clarification and response-generation workflow search your indexed sources.
            </p>
          </div>

          <form
            onSubmit={handleAskQuestion}
            className="rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:p-5"
          >
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()

                  if (!searching && question.trim()) {
                    handleAskQuestion(e)
                  }
                }
              }}
              placeholder={
                pendingConversationId
                  ? 'Enter the additional details requested above...'
                  : 'Ask something about your uploaded documents...'
              }
              className="min-h-32 w-full resize-y bg-transparent text-sm leading-7 text-slate-200 outline-none placeholder:text-slate-600"
            />

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-3">
              <span className="flex items-center gap-2 text-xs text-slate-500">
                <Search size={14} />
                Hybrid retrieval · Qdrant
              </span>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={startVoiceInput}
                  disabled={searching || isListening}
                  className="flex items-center gap-2 rounded-xl border border-cyan-500/30 px-3 py-2.5 text-xs font-medium text-cyan-300 transition hover:bg-cyan-500/10 disabled:opacity-50"
                  title="Speak your question"
                >
                  <Mic size={15} />
                  {isListening ? 'Listening...' : 'Voice input'}
                </button>
                {isListening && <span className="text-xs text-cyan-300">Speak now...</span>}
              </div>

              <button
                type="submit"
                disabled={!question.trim() || searching}
                className="flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {searching ? (
                  <>
                    <Loader2
                      size={16}
                      className="animate-spin"
                    />
                    Searching...
                  </>
                ) : (
                  <>
                    {pendingConversationId ? 'Submit clarification' : 'Search documents'}
                    <Send size={15} />
                  </>
                )}
              </button>
            </div>
          </form>

          {voiceError && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-200">
              {voiceError}
            </div>
          )}

          {/* EXAMPLE QUESTIONS */}

          <div>
            <div className="mb-3 flex items-center gap-2">
              <Sparkles
                size={15}
                className="text-violet-400"
              />

              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Try an example
              </p>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              {exampleQuestions.map(example => (
                <button
                  key={example}
                  onClick={() => {
                    setQuestion(example)
                    handleAskQuestion(null, example)
                  }}
                  disabled={searching || Boolean(pendingConversationId)}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-left text-xs text-slate-400 transition hover:border-violet-500/30 hover:bg-slate-900 hover:text-slate-200 disabled:opacity-50"
                >
                  <span>{example}</span>

                  <ArrowUpRight
                    className="shrink-0 text-slate-600"
                    size={15}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* QUERY ERROR */}

          {queryError && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <CircleHelp
                className="mt-0.5 shrink-0 text-amber-400"
                size={18}
              />

              <p className="text-sm leading-6 text-amber-200">
                {queryError}
              </p>
            </div>
          )}

          {/* LOADING STATE */}

          {searching && (
            <div className="flex items-center gap-3 rounded-xl border border-violet-500/20 bg-violet-500/5 p-5">
              <Loader2
                className="animate-spin text-violet-400"
                size={22}
              />

              <div>
                <p className="text-sm font-medium text-slate-200">
                  Searching your knowledge base
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Understanding your question, retrieving evidence and preparing a grounded response...
                </p>
              </div>
            </div>
          )}

          {/* CLARIFICATION REQUEST */}

          {clarificationMessage && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5">
              <div className="flex items-center gap-2">
                <CircleHelp
                  className="text-amber-300"
                  size={18}
                />
                <p className="text-sm font-semibold text-amber-200">
                  A little more detail is needed
                </p>
              </div>

              <p className="mt-2 text-sm leading-6 text-amber-100/90">
                {clarificationMessage}
              </p>

              {pendingConversationId && (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <p className="min-w-0 break-words text-xs text-amber-200/70">
                    Original question: {pendingOriginalQuestion}
                  </p>

                  <button
                    type="button"
                    onClick={cancelClarification}
                    disabled={searching}
                    className="shrink-0 rounded-lg border border-amber-500/30 px-3 py-2 text-xs font-medium text-amber-200 transition hover:bg-amber-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancel clarification
                  </button>
                </div>
              )}
            </div>
          )}

          {/* GENERATED ANSWER */}

          {generatedAnswer && (
            <div className="rounded-2xl border border-violet-500/30 bg-gradient-to-br from-violet-500/10 to-slate-900 p-5 sm:p-6">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles
                  className="text-violet-300"
                  size={18}
                />
                <h3 className="text-sm font-semibold text-violet-200">
                  AI-generated response
                </h3>
                <span className="ml-auto rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-300">
                  Grounded in retrieved evidence
                </span>
                <button
                  type="button"
                  onClick={isSpeaking ? stopSpeaking : speakAnswer}
                  className="flex items-center gap-1.5 rounded-lg border border-violet-500/30 px-3 py-2 text-xs text-violet-200 hover:bg-violet-500/10"
                >
                  {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                  {isSpeaking ? 'Stop' : 'Read aloud'}
                </button>
              </div>

              <div className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-200">
                {generatedAnswer}
              </div>
            </div>
          )}

          {/* GENERATION SERVICE NOTICE */}

          {generationNotice && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <CircleHelp
                className="mt-0.5 shrink-0 text-amber-400"
                size={18}
              />
              <p className="text-sm leading-6 text-amber-200">
                {generationNotice}
              </p>
            </div>
          )}

          {/* RETRIEVED RESULTS */}

          {queryResults.length > 0 && (
            <div className="space-y-5">

              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-violet-400">
                    Search results
                  </p>

                  <h3 className="text-xl font-semibold">
                    Retrieved evidence
                  </h3>

                  <p className="mt-2 max-w-2xl break-words text-sm leading-6 text-slate-400">
                    Results for: "{searchedQuestion}"
                  </p>
                </div>

                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5 text-xs text-emerald-300">
                  {queryResults.length} passage(s) retrieved
                </span>
              </div>

              <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                <div className="flex items-center gap-2">
                  <BrainCircuit
                    className="text-cyan-300"
                    size={17}
                  />

                  <p className="text-sm font-medium text-cyan-300">
                    Retrieved source evidence
                  </p>
                </div>

                <p className="mt-2 text-xs leading-6 text-slate-400">
                  These passages were selected by the retrieval agent from your indexed
                  knowledge base. Review the original source content to verify the response.
                  Structured CSV records are displayed in tables.
                </p>
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-300">
                  <span className="rounded-lg border border-cyan-500/20 bg-slate-950/40 px-3 py-2">
                    Retrieved passages: {queryResults.length}
                  </span>
                  <span className="rounded-lg border border-cyan-500/20 bg-slate-950/40 px-3 py-2">
                    Retrieval confidence: {typeof retrievalConfidence === 'number' ? `${(retrievalConfidence * 100).toFixed(1)}%` : 'Not supplied by API'}
                  </span>
                  <span className="rounded-lg border border-cyan-500/20 bg-slate-950/40 px-3 py-2">
                    Cited sources: {answerSources.length}
                  </span>
                </div>
                {answerSources.length > 0 && (
                  <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <p className="mb-2 text-xs font-semibold text-slate-300">Answer source references</p>
                    <div className="flex flex-wrap gap-2">
                      {answerSources.map((source, sourceIndex) => (
                        <span key={`${source.source_id || sourceIndex}-${source.filename || ''}`} className="rounded-md border border-violet-500/20 px-2.5 py-1.5 text-xs text-violet-200">
                          {source.source_id || `Source ${sourceIndex + 1}`} · {source.filename || 'Document'} · chunk {source.chunk_index ?? 'N/A'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                {queryResults.map((result, index) =>
                  renderResultCard(result, index)
                )}
              </div>

              <button
                onClick={() => navigateTo('Retrieval Explorer')}
                className="flex items-center gap-2 text-sm text-violet-400 transition hover:text-violet-300"
              >
                Explore retrieval results
                <ArrowUpRight size={15} />
              </button>
            </div>
          )}

          <p className="text-center text-xs text-slate-600">
            Powered by sentence embeddings, hybrid retrieval and Qdrant.
          </p>
        </div>
      )
    }

    // ================================================
    // RETRIEVAL EXPLORER
    // ================================================

    if (activePage === 'Retrieval Explorer') {
      return (
        <div className="space-y-6">

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-violet-500/10 p-3">
                  <Search
                    className="text-violet-400"
                    size={23}
                  />
                </div>

                <div>
                  <h2 className="font-semibold">
                    Retrieval Explorer
                  </h2>

                  <p className="mt-1 text-sm text-slate-400">
                    Inspect the latest retrieval operation.
                  </p>
                </div>
              </div>

              <button
                onClick={() => navigateTo('Ask Documents')}
                className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm text-white transition hover:bg-violet-500"
              >
                New search
                <ArrowUpRight size={15} />
              </button>
            </div>

            {searchedQuestion ? (
              <div className="mt-6 rounded-xl border border-slate-800 bg-[#090d18] p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Latest search query
                </p>

                <p className="mt-2 break-words text-sm leading-6 text-slate-200">
                  {searchedQuestion}
                </p>

                <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                  <span>
                    {queryResults.length} retrieved passage(s)
                  </span>

                  <span>Top-K: 5</span>
                </div>
              </div>
            ) : (
              <div className="mt-6 rounded-xl border border-dashed border-slate-700 p-8 text-center">
                <Filter
                  className="mx-auto mb-3 text-slate-600"
                  size={28}
                />

                <p className="text-sm text-slate-400">
                  No retrieval operation to inspect yet.
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Run a search from Ask Documents to view its results here.
                </p>
              </div>
            )}
          </div>

          {queryResults.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">
                  Retrieved passages
                </h3>

                <span className="text-xs text-slate-500">
                  Latest search
                </span>
              </div>

              {queryResults.map((result, index) =>
                renderResultCard(result, index)
              )}
            </div>
          )}

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="mb-4 font-semibold">
              Retrieval configuration
            </h3>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs text-slate-500">
                  Vector database
                </p>

                <p className="mt-2 font-medium text-violet-300">
                  Qdrant
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs text-slate-500">
                  Embedding model
                </p>

                <p className="mt-2 font-medium text-cyan-300">
                  all-MiniLM-L6-v2
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs text-slate-500">
                  Vector dimensions
                </p>

                <p className="mt-2 font-medium text-slate-200">
                  384
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs text-slate-500">
                  Requested result limit
                </p>

                <p className="mt-2 font-medium text-slate-200">
                  Top 5
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    }

    // ================================================
    // EVALUATION
    // ================================================

    if (activePage === 'Evaluation') {
      return (
        <div className="space-y-5">

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-violet-500/10 p-3">
                <Activity
                  className="text-violet-400"
                  size={23}
                />
              </div>

              <div>
                <h2 className="font-semibold">
                  Retrieval Evaluation
                </h2>

                <p className="mt-1 text-sm text-slate-400">
                  Evaluation metrics and test-query performance
                </p>
              </div>
            </div>

            <div className="mt-6 rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
              <div className="flex items-center gap-2">
                <CircleHelp
                  className="text-amber-300"
                  size={18}
                />

                <p className="text-sm font-medium text-amber-300">
                  Evaluation dataset not configured
                </p>
              </div>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                Retrieval evaluation metrics such as Precision@K, Recall@K,
                MRR and Hit@K require a labelled test dataset and an evaluation
                run. No evaluation scores are being reported until those tests
                have been performed.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="text-sm text-slate-400">
                Retrieval database
              </p>

              <p className="mt-3 text-xl font-semibold text-emerald-400">
                Qdrant
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Vector storage and similarity search
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="text-sm text-slate-400">
                Embedding model
              </p>

              <p className="mt-3 text-xl font-semibold text-cyan-400">
                MiniLM-L6-v2
              </p>

              <p className="mt-1 text-xs text-slate-500">
                384-dimensional embeddings
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="mb-4 font-semibold">
              Suggested evaluation metrics
            </h3>

            {[
              [
                'Precision@K',
                'Measures how many retrieved results are relevant.',
              ],
              [
                'Recall@K',
                'Measures how many relevant items were retrieved.',
              ],
              [
                'MRR',
                'Measures the ranking position of the first relevant result.',
              ],
              [
                'Hit@K',
                'Checks whether at least one relevant result appears in the top K.',
              ],
            ].map(([name, description]) => (
              <div
                key={name}
                className="border-b border-slate-800 py-3 last:border-0"
              >
                <p className="text-sm font-medium text-slate-200">
                  {name}
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )
    }

    // ================================================
    // OVERVIEW
    // ================================================

    return (
      <div className="space-y-6">

        {/* STATISTICS */}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map(stat => {
            const Icon = stat.icon

            return (
              <div
                key={stat.label}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700"
              >
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-2.5 ${stat.bg}`}>
                    <Icon
                      className={stat.color}
                      size={20}
                    />
                  </div>

                  <ArrowUpRight
                    className="text-slate-600"
                    size={17}
                  />
                </div>

                <p className="mt-5 text-2xl font-semibold tracking-tight">
                  {stat.value}
                </p>

                <p className="mt-1 text-sm font-medium text-slate-300">
                  {stat.label}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {stat.detail}
                </p>
              </div>
            )
          })}
        </div>

        <div className="grid gap-5 xl:grid-cols-3">

          <div className="space-y-5 xl:col-span-2">

            {/* KNOWLEDGE BASE SUMMARY */}

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold">
                    Knowledge base
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Documents processed in this session
                  </p>
                </div>

                <button
                  onClick={() => navigateTo('Knowledge Base')}
                  className="text-sm text-violet-400 transition hover:text-violet-300"
                >
                  View all
                  <ChevronRight
                    className="inline"
                    size={15}
                  />
                </button>
              </div>

              {uploadedDocuments.length === 0 ? (
                <div className="border-t border-slate-800 py-7 text-center">
                  <Files
                    className="mx-auto mb-2 text-slate-600"
                    size={26}
                  />

                  <p className="text-sm text-slate-400">
                    Your session document list is empty.
                  </p>

                  <button
                    onClick={() => navigateTo('Knowledge Base')}
                    className="mt-3 text-xs text-violet-400 hover:text-violet-300"
                  >
                    Upload your first document
                  </button>
                </div>
              ) : (
                uploadedDocuments.slice(0, 5).map(doc => (
                  <div
                    key={doc.storedFilename}
                    className="flex items-center gap-3 border-t border-slate-800 py-3"
                  >
                    <div className="rounded-lg bg-violet-500/10 p-2">
                      <FileText
                        className="text-violet-400"
                        size={18}
                      />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {doc.name}
                      </p>

                      <p className="text-xs text-slate-500">
                        {doc.chunks} chunks indexed
                      </p>
                    </div>

                    <span className="flex items-center gap-1 text-xs text-emerald-400">
                      <CheckCircle2 size={14} />
                      {doc.status}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* PROCESSING PIPELINE */}

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="font-semibold">
                  Knowledge processing pipeline
                </h2>

                <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                  Core pipeline implemented
                </span>
              </div>

              {[
                [
                  'Document text extraction',
                  'PDF · DOCX · TXT · CSV',
                ],
                [
                  'Text cleaning and chunking',
                  'Structured CSV chunking supported',
                ],
                [
                  'Embedding generation',
                  'all-MiniLM-L6-v2',
                ],
                [
                  'Vector indexing',
                  'Qdrant',
                ],
                [
                  'Information retrieval',
                  'Query-based retrieval',
                ],
              ].map(([item, detail]) => (
                <div
                  key={item}
                  className="flex items-center gap-3 border-b border-slate-800 py-3 last:border-0"
                >
                  <CheckCircle2
                    size={17}
                    className="shrink-0 text-emerald-400"
                  />

                  <div className="min-w-0">
                    <p className="text-sm text-slate-300">
                      {item}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {detail}
                    </p>
                  </div>

                  <span className="ml-auto shrink-0 text-xs text-emerald-400">
                    Ready
                  </span>
                </div>
              ))}
            </div>

            {/* QUERY HISTORY */}

            {queryHistory.length > 0 && (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-semibold">
                    Recent queries
                  </h2>

                  <span className="text-xs text-slate-500">
                    This session
                  </span>
                </div>

                {queryHistory.slice(0, 4).map((item, index) => (
                  <button
                    key={`${item.question}-${index}`}
                    onClick={() => {
                      setQuestion(item.question)
                      navigateTo('Ask Documents')
                    }}
                    className="flex w-full items-center gap-3 border-t border-slate-800 py-3 text-left transition hover:bg-slate-800/30"
                  >
                    <Clock3
                      className="shrink-0 text-slate-500"
                      size={16}
                    />

                    <span className="min-w-0 flex-1 truncate text-sm text-slate-300">
                      {item.question}
                    </span>

                    <span className="shrink-0 text-xs text-slate-500">
                      {item.time}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* RIGHT SIDEBAR */}

          <div className="space-y-5">

            {/* AI WORKSPACE */}

            <div className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-slate-900 p-5">
              <div className="mb-3 flex items-center gap-2 text-violet-300">
                <Sparkles size={18} />
                <span className="text-sm font-medium">
                  AI Workspace
                </span>
              </div>

              <h2 className="text-lg font-semibold">
                Explore your knowledge
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                Search your documents and discover relevant information using
                the knowledge retrieval pipeline.
              </p>

              <button
                onClick={() => navigateTo('Ask Documents')}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-violet-500"
              >
                Ask a question
                <ArrowUpRight size={16} />
              </button>
            </div>

            {/* SYSTEM COMPONENTS */}

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="mb-4 font-semibold">
                System components
              </h2>

              <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-2">
                  <Server
                    size={15}
                    className="text-slate-500"
                  />

                  <span className="text-sm text-slate-400">
                    Frontend
                  </span>
                </div>

                <span className="text-xs text-emerald-400">
                  Running
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800 py-3">
                <div className="flex items-center gap-2">
                  <Database
                    size={15}
                    className="text-slate-500"
                  />

                  <span className="text-sm text-slate-400">
                    Vector database
                  </span>
                </div>

                <span className="text-xs text-emerald-400">
                  Configured
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800 py-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit
                    size={15}
                    className="text-slate-500"
                  />

                  <span className="text-sm text-slate-400">
                    Embeddings
                  </span>
                </div>

                <span className="text-xs text-emerald-400">
                  Configured
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800 py-3">
                <span className="text-sm text-slate-400">
                  Agent orchestration
                </span>

                <span className="text-xs text-amber-400">
                  Planned
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800 py-3">
                <span className="text-sm text-slate-400">
                  Answer generation
                </span>

                <span className="text-xs text-amber-400">
                  Not integrated
                </span>
              </div>
            </div>

            {/* SESSION ACTIVITY */}

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <div className="flex items-center gap-2">
                <Activity
                  size={17}
                  className="text-violet-400"
                />

                <h2 className="font-semibold">
                  Session activity
                </h2>
              </div>

              <div className="mt-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">
                    Documents processed
                  </span>

                  <span className="text-slate-200">
                    {uploadedDocuments.length}
                  </span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">
                    Chunks processed
                  </span>

                  <span className="text-slate-200">
                    {totalChunks}
                  </span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">
                    Queries executed
                  </span>

                  <span className="text-slate-200">
                    {queryCount}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // --------------------------------------------------
  // MAIN LAYOUT
  // --------------------------------------------------

  return (
    <div className="min-h-screen bg-[#090d18] text-slate-100">

      {/* MOBILE MENU OVERLAY */}

      {mobileMenu && (
        <button
          aria-label="Close menu"
          onClick={() => setMobileMenu(false)}
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
        />
      )}

      {/* SIDEBAR */}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-800 bg-[#0c1120] transition-transform lg:translate-x-0 ${
          mobileMenu
            ? 'translate-x-0'
            : '-translate-x-full'
        }`}
      >
        <div className="flex h-20 items-center justify-between border-b border-slate-800 px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-violet-600 p-2">
              <Sparkles size={20} />
            </div>

            <div>
              <p className="font-semibold tracking-tight">
                Nexus AI
              </p>

              <p className="text-[10px] tracking-widest text-slate-500">
                KNOWLEDGE PLATFORM
              </p>
            </div>
          </div>

          <button
            onClick={() => setMobileMenu(false)}
            className="text-slate-400 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-3 text-[10px] font-semibold tracking-[0.18em] text-slate-500">
            WORKSPACE
          </p>

          <nav className="space-y-1">
            {navigation.map(({ name, icon: Icon }) => (
              <button
                key={name}
                onClick={() => navigateTo(name)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${
                  activePage === name
                    ? 'bg-violet-500/15 font-medium text-violet-300'
                    : 'text-slate-400 hover:bg-slate-800/70 hover:text-white'
                }`}
              >
                <Icon size={18} />

                {name}

                {activePage === name && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400" />
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* SIDEBAR FOOTER */}

        <div className="mt-auto border-t border-slate-800 p-4">
          <div className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-500">
            <Settings size={18} />
            Project workspace
          </div>

          <div className="mt-3 flex items-center gap-3 rounded-xl bg-slate-900 p-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 text-sm font-bold">
              N
            </div>

            <div>
              <p className="text-sm font-medium">
                Workspace
              </p>

              <p className="text-xs text-slate-500">
                Knowledge platform
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}

      <main className="min-h-screen lg:pl-64">

        {/* HEADER */}

        <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-800/80 bg-[#090d18]/90 px-5 backdrop-blur-xl sm:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenu(true)}
              className="text-slate-400 lg:hidden"
              aria-label="Open menu"
            >
              <Menu />
            </button>

            <div>
              <h1 className="text-lg font-semibold">
                {activePage}
              </h1>

              <p className="hidden text-xs text-slate-500 sm:block">
                AI-powered knowledge retrieval workspace
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-2 sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              <span className="text-xs text-slate-400">
                Workspace active
              </span>
            </div>

            <button
              onClick={() => navigateTo('Overview')}
              aria-label="Go to overview"
              className="rounded-xl border border-slate-800 p-2.5 text-slate-400 transition hover:bg-slate-800"
            >
              <LayoutDashboard size={18} />
            </button>
          </div>
        </header>

        {/* PAGE BODY */}

        <div className="mx-auto max-w-[1500px] p-5 sm:p-8">
          <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
                NEXUS / WORKSPACE
              </p>

              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {activePage === 'Overview'
                  ? 'Welcome to your knowledge hub'
                  : activePage}
              </h2>

              <p className="mt-2 text-sm text-slate-400">
                {pageDescriptions[activePage]}
              </p>
            </div>

            {activePage === 'Overview' && (
              <button
                onClick={() => navigateTo('Knowledge Base')}
                className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-violet-950/30 transition hover:bg-violet-500"
              >
                <Plus size={17} />
                Add documents
              </button>
            )}
          </div>

          {renderContent()}

          {/* FOOTER */}

          <footer className="mt-10 border-t border-slate-800 pt-5 text-center text-xs text-slate-600">
            Nexus AI · Knowledge Retrieval Platform · React · FastAPI · Qdrant
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
