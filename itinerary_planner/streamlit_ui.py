"""
Travel Planner Streamlit UI

A beautiful frontend for the Multi-Agent Travel Planner system.
"""

import streamlit as st
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from itinerary_planner.itinerary_agent import itinerary_agent


# Page configuration
st.set_page_config(
    page_title="✈️ AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .stTextArea textarea {
        font-size: 1.1rem;
    }
    
    .result-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .agent-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: linear-gradient(90deg, #11998e, #38ef7d);
        color: white;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 0.2rem;
    }
    
    .price-tag {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e7d32;
    }
    
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<h1 class="main-header">✈️ AI Travel Planner</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Powered by Google A2A Protocol, ADK, and MCP</p>',
        unsafe_allow_html=True
    )
    
    # Sidebar with agent information
    with st.sidebar:
        st.header("🤖 Multi-Agent System")
        st.markdown("---")
        
        st.subheader("Active Agents")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🎯 **Host Agent**")
            st.caption("Itinerary Planner")
            st.caption("Port: 8005")
        
        with col2:
            st.markdown("✈️ **Flight Agent**")
            st.caption("ADK + Gemini")
            st.caption("Port: 8000")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🏨 **Hotel Agent**")
            st.caption("LangChain + GPT-4o")
            st.caption("Port: 8003")
        
        with col2:
            st.markdown("🔗 **Protocol**")
            st.caption("A2A + MCP")
        
        st.markdown("---")
        st.subheader("How it works")
        st.markdown("""
        1. 📝 Enter your travel request
        2. 🔄 Host agent parses request
        3. ✈️ Flight agent searches flights
        4. 🏨 Hotel agent searches hotels
        5. 📋 Results synthesized into itinerary
        """)
    
    # Main content area
    st.markdown("### 📝 Describe Your Trip")
    
    # Example requests
    examples = [
        "Plan a trip to Paris from New York, July 10-20, 2025",
        "I want to visit Tokyo from San Francisco for a week in September",
        "Book a romantic getaway to Bali from Los Angeles, 5 nights in December",
        "Family vacation to London from Chicago, August 15-25, 4 people"
    ]
    
    selected_example = st.selectbox(
        "Or choose an example:",
        ["-- Select an example --"] + examples
    )
    
    travel_request = st.text_area(
        "Enter your travel request:",
        value=selected_example if selected_example != "-- Select an example --" else "",
        height=100,
        placeholder="e.g., Plan a trip to Paris from New York, July 10-20, 2025"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        plan_button = st.button("🚀 Plan My Trip", use_container_width=True, type="primary")
    
    # Process the request
    if plan_button and travel_request:
        st.markdown("---")
        
        with st.spinner("🔄 Processing your travel request..."):
            # Create progress indicators
            progress_container = st.container()
            
            with progress_container:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status1 = st.empty()
                    status1.info("⏳ Parsing request...")
                
                with col2:
                    status2 = st.empty()
                    status2.info("⏳ Waiting for flights...")
                
                with col3:
                    status3 = st.empty()
                    status3.info("⏳ Waiting for hotels...")
            
            # Run the async planning
            try:
                result = asyncio.run(itinerary_agent.plan_trip(travel_request))
                
                # Update status indicators
                status1.success("✅ Request parsed")
                status2.success("✅ Flights found")
                status3.success("✅ Hotels found")
                
                if result.get("status") == "success":
                    st.markdown("---")
                    
                    # Display parsed parameters
                    st.subheader("📍 Trip Details")
                    params = result.get("parsed_parameters", {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("From", params.get("origin", "N/A"))
                    with col2:
                        st.metric("To", params.get("destination", "N/A"))
                    with col3:
                        st.metric("Departure", params.get("departure_date", "N/A"))
                    with col4:
                        st.metric("Return", params.get("return_date", "N/A"))
                    
                    st.markdown("---")
                    
                    # Display flight results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("✈️ Flight Options")
                        flight_data = result.get("flight_results", {})
                        
                        if "data" in flight_data and "flights" in flight_data["data"]:
                            flights = flight_data["data"]["flights"][:3]
                            for i, flight in enumerate(flights):
                                with st.expander(f"Option {i+1}: {flight.get('airline', 'N/A')} - ${flight.get('price', 'N/A')}", expanded=(i==0)):
                                    st.write(f"**Flight:** {flight.get('flight_id', 'N/A')}")
                                    st.write(f"**Route:** {flight.get('origin', '')} → {flight.get('destination', '')}")
                                    st.write(f"**Departure:** {flight.get('departure_time', 'N/A')}")
                                    st.write(f"**Duration:** {flight.get('duration', 'N/A')}")
                                    st.write(f"**Stops:** {flight.get('stops', 0)}")
                        elif "summary" in flight_data:
                            st.write(flight_data["summary"])
                        else:
                            st.warning("No flight data available")
                    
                    with col2:
                        st.subheader("🏨 Hotel Options")
                        hotel_data = result.get("hotel_results", {})
                        
                        if "data" in hotel_data and "hotels" in hotel_data["data"]:
                            hotels = hotel_data["data"]["hotels"][:3]
                            for i, hotel in enumerate(hotels):
                                with st.expander(f"Option {i+1}: {hotel.get('name', 'N/A')} - ${hotel.get('price_per_night', 'N/A')}/night", expanded=(i==0)):
                                    st.write(f"**Rating:** {'⭐' * hotel.get('star_rating', 0)} ({hotel.get('user_rating', 'N/A')}/5)")
                                    st.write(f"**Room Type:** {hotel.get('room_type', 'N/A')}")
                                    st.write(f"**Amenities:** {', '.join(hotel.get('amenities', [])[:5])}")
                                    st.write(f"**Breakfast:** {'✅ Included' if hotel.get('breakfast_included') else '❌ Not included'}")
                        elif "summary" in hotel_data:
                            st.write(hotel_data["summary"])
                        else:
                            st.warning("No hotel data available")
                    
                    st.markdown("---")
                    
                    # Display the synthesized itinerary
                    st.subheader("📋 Your Complete Itinerary")
                    st.markdown(result.get("itinerary", "No itinerary generated"))
                    
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                status1.error("❌ Error")
                status2.error("❌ Error")
                status3.error("❌ Error")
                st.error(f"An error occurred: {str(e)}")
    
    elif plan_button:
        st.warning("Please enter a travel request first!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.9rem;">
            Built with ❤️ using Google A2A Protocol, ADK, MCP, and Streamlit<br>
            Multi-Agent Architecture: Itinerary Planner → Flight Agent + Hotel Agent
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
