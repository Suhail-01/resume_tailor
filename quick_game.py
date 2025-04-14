import streamlit as st
import random
import string
import time
import json
import os
from datetime import datetime, timedelta

# Game configuration
DEFAULT_TIME_LIMIT = 3  # Default time limit in minutes
CATEGORIES = {
    "Animals": ["dog", "cat", "elephant", "tiger", "penguin", "giraffe", "dolphin", "koala"],
    "Countries": ["france", "japan", "brazil", "canada", "egypt", "australia", "india", "mexico"],
    "Foods": ["pizza", "sushi", "pasta", "burger", "chocolate", "taco", "salad", "pancake"],
    "Movies": ["avatar", "inception", "titanic", "frozen", "jaws", "batman", "matrix", "gladiator"]
}
HINTS = {
    "Animals": {
        "dog": ["Man's best friend", "Barks", "Common pet"],
        "cat": ["Meows", "Independent pet", "Often purrs"],
        "elephant": ["Largest land mammal", "Has a trunk", "Gray and wrinkly"],
        "tiger": ["Big cat with stripes", "Orange and black", "Lives in Asia"],
        "penguin": ["Flightless bird", "Lives in Antarctica", "Black and white"],
        "giraffe": ["Long neck", "Tallest animal", "Spotted coat"],
        "dolphin": ["Marine mammal", "Intelligent", "Breathes air"],
        "koala": ["Lives in Australia", "Eats eucalyptus", "Often sleeps"]
    },
    "Countries": {
        "france": ["Known for Eiffel Tower", "European country", "Famous for wine and cheese"],
        "japan": ["Island nation in Asia", "Land of the rising sun", "Known for sushi and anime"],
        "brazil": ["Largest country in South America", "Famous for carnival", "Home of the Amazon rainforest"],
        "canada": ["Second largest country by area", "Maple leaf flag", "Known for maple syrup"],
        "egypt": ["Home of the pyramids", "Located in North Africa", "Ancient civilization along the Nile"],
        "australia": ["Continent and country", "Known for kangaroos", "Has the Great Barrier Reef"],
        "india": ["Second most populous country", "Known for Taj Mahal", "South Asian country"],
        "mexico": ["North American country", "Known for tacos", "Celebrates Day of the Dead"]
    },
    "Foods": {
        "pizza": ["Italian dish", "Round with toppings", "Often has cheese and tomato sauce"],
        "sushi": ["Japanese dish", "Often contains raw fish", "Wrapped in seaweed and rice"],
        "pasta": ["Italian staple food", "Made from wheat flour", "Many shapes and varieties"],
        "burger": ["Fast food sandwich", "Has a patty", "Between two buns"],
        "chocolate": ["Made from cocoa beans", "Sweet treat", "Can be dark, milk, or white"],
        "taco": ["Mexican dish", "Folded tortilla", "Various fillings"],
        "salad": ["Often contains vegetables", "Usually healthy", "Can be a side or main dish"],
        "pancake": ["Breakfast food", "Flat and round", "Often topped with syrup"]
    },
    "Movies": {
        "avatar": ["Blue aliens", "Directed by James Cameron", "Highest-grossing film at its time"],
        "inception": ["Dreams within dreams", "Directed by Christopher Nolan", "Spinning top at the end"],
        "titanic": ["Famous ship disaster", "Leonardo DiCaprio and Kate Winslet", "Heart will go on song"],
        "frozen": ["Let it go song", "Disney princess movie", "Talking snowman"],
        "jaws": ["Killer shark", "Directed by Steven Spielberg", "Beach town terrorized"],
        "batman": ["Superhero in Gotham", "Dark Knight", "Wears a cape and mask"],
        "matrix": ["Red pill or blue pill", "Neo is the chosen one", "Slow-motion bullet time"],
        "gladiator": ["Ancient Rome", "Russell Crowe", "Arena fights"]
    }
}

def generate_game_id():
    """Generate a unique 6-character game ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_word(category):
    """Generate a random word from the selected category"""
    return random.choice(CATEGORIES[category])

def get_hint(category, word, hint_level):
    """Get a hint for the current word"""
    if hint_level < len(HINTS[category][word]):
        return HINTS[category][word][hint_level]
    return "No more hints available!"

def save_game_state(game_id, game_state):
    """Save game state to session state"""
    if 'games' not in st.session_state:
        st.session_state.games = {}
    st.session_state.games[game_id] = game_state

def load_game_state(game_id):
    """Load game state from session state"""
    if 'games' in st.session_state and game_id in st.session_state.games:
        return st.session_state.games[game_id]
    return None

def set_page_config():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="Quick Word Game",
        page_icon="🎮",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

def main():
    # Set page configuration
    set_page_config()
    
    st.title("⏱️ Quick Word Game")
    st.subheader("A fast-paced multiplayer game for people short on time")
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("How to Play")
        st.markdown("""
        1. **Host a Game**: Create a new game and share the game ID with friends
        2. **Join a Game**: Enter a game ID to join an existing game
        3. **Play**: Guess the word based on the category and hints
        4. **Win**: First player to guess correctly wins!
        
        No account needed, no downloads required!
        """)
    
    # Main page tabs
    tab1, tab2 = st.tabs(["Start/Join Game", "About"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        # Create a new game
        with col1:
            st.header("Create a New Game")
            
            category = st.selectbox(
                "Select a category",
                list(CATEGORIES.keys())
            )
            
            time_limit = st.slider(
                "Time limit (minutes)",
                min_value=1,
                max_value=10,
                value=DEFAULT_TIME_LIMIT,
                step=1
            )
            
            if st.button("Create Game", type="primary"):
                game_id = generate_game_id()
                word = generate_word(category)
                
                # Create game state
                game_state = {
                    "category": category,
                    "word": word,
                    "created_at": datetime.now().isoformat(),
                    "time_limit_minutes": time_limit,
                    "host": True,
                    "players": {},
                    "guesses": [],
                    "hint_level": 0,
                    "winner": None,
                    "game_over": False
                }
                
                # Save game state
                save_game_state(game_id, game_state)
                
                # Set current game
                st.session_state.current_game_id = game_id
                st.session_state.player_name = "Host"
                
                # Rerun to show game screen
                st.rerun()
        
        # Join an existing game
        with col2:
            st.header("Join an Existing Game")
            
            game_id = st.text_input(
                "Enter game ID",
                max_chars=6
            ).upper()
            
            player_name = st.text_input(
                "Your name",
                max_chars=20
            )
            
            if st.button("Join Game", type="primary"):
                if not game_id:
                    st.error("Please enter a game ID")
                elif not player_name:
                    st.error("Please enter your name")
                else:
                    # Check if game exists in our session state
                    game_state = load_game_state(game_id)
                    
                    if game_state:
                        # Add player to game
                        game_state["players"][player_name] = {
                            "joined_at": datetime.now().isoformat(),
                            "correct_guesses": 0
                        }
                        
                        # Save updated game state
                        save_game_state(game_id, game_state)
                        
                        # Set current game
                        st.session_state.current_game_id = game_id
                        st.session_state.player_name = player_name
                        
                        # Rerun to show game screen
                        st.rerun()
                    else:
                        st.error(f"Game ID {game_id} not found. Make sure you're using the correct ID.")
    
    with tab2:
        st.header("About Quick Word Game")
        st.markdown("""
        This game is designed for people who:
        - Are short on time but want to play together
        - Don't want to create accounts or download apps
        - Enjoy word games and friendly competition
        
        **Features:**
        - No registration required
        - Play with friends anywhere
        - Multiple categories to choose from
        - Hints available when you get stuck
        - Timed games for quick fun
        
        Have fun playing!
        """)
    
    # Check if user is in a game
    if 'current_game_id' in st.session_state:
        game_id = st.session_state.current_game_id
        game_state = load_game_state(game_id)
        
        if game_state:
            display_game(game_id, game_state)

def display_game(game_id, game_state):
    """Display the game screen"""
    # Create container for game area
    game_container = st.container()
    
    with game_container:
        # Game header with info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.header(f"Game: {game_id}")
            st.subheader(f"Category: {game_state['category']}")
        
        with col2:
            # Calculate time remaining
            created_at = datetime.fromisoformat(game_state['created_at'])
            time_limit = timedelta(minutes=game_state['time_limit_minutes'])
            end_time = created_at + time_limit
            remaining = end_time - datetime.now()
            
            # Display time remaining
            if remaining.total_seconds() > 0 and not game_state['game_over']:
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                st.metric("Time Left", f"{minutes}:{seconds:02d}")
            else:
                if not game_state['game_over']:
                    # Time's up, end the game
                    game_state['game_over'] = True
                    save_game_state(game_id, game_state)
                
                st.metric("Time Left", "0:00")
        
        with col3:
            # Display players in the game
            st.metric("Players", len(game_state['players']) + 1 if 'host' in game_state and game_state['host'] else len(game_state['players']))
            
            # Create a share button/link
            st.button(
                "Share Game ID",
                help=f"Share this Game ID with friends: {game_id}",
                on_click=lambda: st.clipboard.set_clipboard_text(game_id)
            )
        
        # Display word to guess (with blanks)
        st.divider()
        
        word = game_state['word']
        word_display = ""
        
        if game_state['game_over'] or 'winner' in game_state and game_state['winner']:
            # If game is over, show the word
            word_display = word.upper()
        else:
            # Otherwise show blanks
            for c in word:
                if c.isalpha():
                    word_display += "_ "
                else:
                    word_display += c + " "
        
        st.markdown(f"<h1 style='text-align: center;'>{word_display}</h1>", unsafe_allow_html=True)
        
        # Display hints
        hint_col, guess_col = st.columns([1, 2])
        
        with hint_col:
            st.subheader("Need a hint?")
            
            if st.button("Get Hint") and not game_state['game_over']:
                # Increment hint level
                game_state['hint_level'] += 1
                save_game_state(game_id, game_state)
                st.rerun()
            
            # Display current hint
            if game_state['hint_level'] > 0:
                for i in range(game_state['hint_level']):
                    hint = get_hint(game_state['category'], game_state['word'], i)
                    st.info(f"Hint {i+1}: {hint}")
        
        # Guess input form
        with guess_col:
            st.subheader("Make a guess")
            
            # Only allow guesses if game is not over
            if not game_state['game_over'] and 'winner' not in game_state:
                with st.form("guess_form", clear_on_submit=True):
                    guess = st.text_input("Your guess", key="guess_input")
                    submitted = st.form_submit_button("Submit Guess")
                    
                    if submitted and guess:
                        player_name = st.session_state.player_name
                        
                        # Record the guess
                        game_state['guesses'].append({
                            "player": player_name,
                            "guess": guess,
                            "timestamp": datetime.now().isoformat(),
                            "correct": guess.lower() == word.lower()
                        })
                        
                        # Check if guess is correct
                        if guess.lower() == word.lower():
                            game_state['winner'] = player_name
                            game_state['game_over'] = True
                        
                        save_game_state(game_id, game_state)
                        st.rerun()
            else:
                if 'winner' in game_state and game_state['winner']:
                    st.success(f"🎉 {game_state['winner']} won the game! The word was: {word.upper()}")
                else:
                    st.warning(f"⏱️ Time's up! The word was: {word.upper()}")
        
        # Display guesses
        st.divider()
        st.subheader("Recent Guesses")
        
        # Create a container for guesses
        guess_container = st.container()
        
        with guess_container:
            # Show last 10 guesses in reverse order (newest first)
            for guess in reversed(game_state['guesses'][-10:] if len(game_state['guesses']) > 10 else game_state['guesses']):
                player = guess['player']
                guess_text = guess['guess']
                correct = guess['correct']
                
                if correct:
                    st.success(f"{player}: {guess_text} ✅")
                else:
                    st.info(f"{player}: {guess_text}")
        
        # New game button
        if game_state['game_over'] or 'winner' in game_state and game_state['winner']:
            if st.button("Start New Game", type="primary"):
                # Clear current game
                del st.session_state.current_game_id
                st.rerun()

if __name__ == "__main__":
    main()