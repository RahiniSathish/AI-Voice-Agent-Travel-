"""
Sidebar Navigation Buttons Component
This module provides a reliable way to create sidebar navigation buttons
"""

import streamlit as st
import requests
import base64
import os
from datetime import datetime

def stop_audio():
    """Stop any playing audio"""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            print("🔇 Audio stopped by button click")
    except Exception as e:
        print(f"🔇 Error stopping audio: {e}")

def create_sidebar_navigation():
    """Create sidebar navigation with working buttons"""
    
    with st.sidebar:
        # Header
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="color: #333333; margin: 0; font-size: 1.5rem;">Attar Travel</h2>
                <p style="color: #666666; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Saudi Arabia Travel Specialist</p>
            </div>
        """, unsafe_allow_html=True)
        
        
        
        # Clean buttons without left column icons
        
        # Dashboard Button (first)
        if st.button("Dashboard", key="btn_dashboard_text", use_container_width=True):
            print("📊 Dashboard button clicked - stopping audio and conversation")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop voice conversation
            st.session_state.current_view = 'dashboard'
            st.session_state.show_bookings = False
            st.session_state.show_chat_history = False
            st.rerun()
        
        # Chat/Conversation Button (removed)
        if False and st.button("Chat", key="btn_chat_main_text", use_container_width=True):
            # Return to conversation view and load chat history from database
            print("💬 Chat button clicked - stopping audio and loading conversation history")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop voice conversation
            
            # Load chat history from backend
            BACKEND_URL = "http://localhost:8000"
            email = st.session_state.get('customer_email')
            if email:
                try:
                    response = requests.get(f"{BACKEND_URL}/chat_history/{email}", timeout=10)
                    print(f"📡 Backend response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        conversations = data.get('conversations', [])
                        print(f"📊 Found {len(conversations)} conversations in database")
                        
                        # Clear and reload chat history
                        st.session_state.chat_history = []
                        
                        if conversations and len(conversations) > 0:
                            for idx, conv in enumerate(conversations):
                                print(f"  📝 Loading conversation {idx + 1}: {conv.get('user_message', '')[:50]}...")
                                
                                # Extract timestamp
                                created_at = conv.get('created_at', '')
                                time_str = ''
                                if created_at:
                                    try:
                                        # Handle different timestamp formats
                                        if ' ' in created_at:
                                            time_str = created_at.split(' ')[1][:5]  # Extract HH:MM
                                        else:
                                            time_str = created_at[:5]
                                    except:
                                        time_str = created_at[:16] if len(created_at) >= 16 else created_at
                                
                                # Add user message
                                user_msg = conv.get('user_message', '')
                                if user_msg:
                                    st.session_state.chat_history.append({
                                        'role': 'User',
                                        'text': user_msg,
                                        'time': time_str
                                    })
                                
                                # Add AI response
                                ai_msg = conv.get('ai_response', '')
                                if ai_msg:
                                    st.session_state.chat_history.append({
                                        'role': 'Alex',
                                        'text': ai_msg,
                                        'time': time_str
                                    })
                            
                            print(f"✅ Successfully loaded {len(st.session_state.chat_history)} messages into chat")
                        else:
                            print("⚠️ No conversations found in database")
                    else:
                        print(f"❌ Failed to fetch chat history: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading chat history: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️ No email found in session state")
            
            st.session_state.current_view = 'conversation'
            st.session_state.show_bookings = False
            st.session_state.show_chat_history = False
            st.rerun()
        
        # My Bookings Button (second)
        if st.button("My Bookings", key="btn_bookings_text", use_container_width=True):
            print("📋 My Bookings button clicked - stopping audio and conversation")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop voice conversation
            st.session_state.show_bookings = not st.session_state.get('show_bookings', False)
            st.rerun()
        
        # Chat History Button (third)
        if st.button("Chat History", key="btn_chat_text", use_container_width=True):
            print("💭 Chat History button clicked - stopping audio and conversation")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop voice conversation
            st.session_state.show_chat_history = not st.session_state.get('show_chat_history', False)
            st.rerun()
        
        # Voice Chat Button (fourth) - NEW LiveKit Integration
        if st.button("Voice Chat", key="btn_voice_chat", use_container_width=True):
            print("Voice Chat button clicked - opening LiveKit voice interface")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop Azure voice conversation
            st.session_state.current_view = 'voice_chat'
            st.session_state.show_bookings = False
            st.session_state.show_chat_history = False
            st.rerun()
        
        # Logout Button (fifth)
        if st.button("Logout", key="btn_logout_text", use_container_width=True):
            print("🚪 Logout button clicked - stopping audio and conversation")
            stop_audio()  # Stop any playing audio
            st.session_state.conversation_running = False  # Stop voice conversation
            for key in list(st.session_state.keys()):
                if key not in ['session_id']:
                    del st.session_state[key]
            st.rerun()
        
        # Separator
        st.markdown("---")
        
        # User Info
        customer_name = st.session_state.get('customer_name', 'Guest')
        customer_email = st.session_state.get('customer_email', 'No email')
        st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.6); border-radius: 8px; color: #333333;">
                <p style="color: #333333; margin: 0 0 0.3rem 0; font-size: 0.9rem; font-weight: bold;">Logged in as:</p>
                <p style="color: #333333; margin: 0; font-size: 0.9rem;">{customer_name}</p>
                <p style="color: #666666; margin: 0; font-size: 0.8rem;">{customer_email}</p>
            </div>
        """, unsafe_allow_html=True)