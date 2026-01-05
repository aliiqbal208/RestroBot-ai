import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [orderItems, setOrderItems] = useState([])
  const [customerName, setCustomerName] = useState('')
  const [tableNumber, setTableNumber] = useState('')
  const [showStartForm, setShowStartForm] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const createSession = async () => {
    try {
      const response = await fetch(`${API_URL}/session/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_name: customerName || null,
          table_number: tableNumber || null,
        }),
      })

      const data = await response.json()
      setSessionId(data.session_id)
      setMessages([
        {
          role: 'assistant',
          content: data.welcome_message,
          timestamp: new Date().toISOString(),
        },
      ])
      setShowStartForm(false)
    } catch (error) {
      console.error('Error creating session:', error)
      alert('Failed to start chat. Please try again.')
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
        }),
      })

      const data = await response.json()

      const botMessage = {
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, botMessage])
      setOrderItems(data.order_items || [])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = () => {
    setSessionId(null)
    setMessages([])
    setOrderItems([])
    setCustomerName('')
    setTableNumber('')
    setShowStartForm(true)
  }

  if (showStartForm) {
    return (
      <div className="app">
        <div className="start-container">
          <div className="start-card">
            <h1>🍽️ RestroBot - AI</h1>
            <p>AI-Powered Restaurant Ordering System</p>
            
            <div className="form-group">
              <label>Your Name (Optional)</label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Enter your name"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Table Number (Optional)</label>
              <input
                type="text"
                value={tableNumber}
                onChange={(e) => setTableNumber(e.target.value)}
                placeholder="e.g., 5"
                className="form-input"
              />
            </div>

            <button onClick={createSession} className="btn btn-primary">
              Start Ordering
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div>
            <h2>🍽️ RestroBot - AI</h2>
            {customerName && <p className="customer-info">Customer: {customerName}</p>}
            {tableNumber && <p className="customer-info">Table: {tableNumber}</p>}
          </div>
          <button onClick={startNewSession} className="btn btn-secondary">
            New Order
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === 'user' ? 'message-user' : 'message-bot'}`}
            >
              <div className="message-content">
                <div className="message-text">{msg.content}</div>
                <div className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message message-bot">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {orderItems.length > 0 && (
          <div className="order-summary">
            <h3>Current Order:</h3>
            <ul>
              {orderItems.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={sendMessage} className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn btn-send">
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
