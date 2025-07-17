import numpy as np
import wave
import os
import struct

def generate_white_noise(duration=60, sample_rate=44100, amplitude=0.3):
    """Générer du bruit blanc"""
    samples = int(duration * sample_rate)
    noise = np.random.normal(0, amplitude, samples)
    return noise

def generate_cafe_ambiance(duration=60, sample_rate=44100):
    """Générer une ambiance de café"""
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)
    
    # Base de bruit rose
    base_noise = np.random.normal(0, 0.1, samples)
    
    # Ajouter des fréquences caractéristiques d'un café
    cafe_freqs = [200, 400, 800, 1200]  # Conversations, machines, etc.
    ambiance = base_noise.copy()
    
    for freq in cafe_freqs:
        wave_component = 0.05 * np.sin(2 * np.pi * freq * t)
        # Modulation aléatoire pour simuler les conversations
        modulation = np.random.normal(1, 0.1, samples)
        ambiance += wave_component * modulation
    
    return np.clip(ambiance, -1, 1)

def generate_forest_ambiance(duration=60, sample_rate=44100):
    """Générer une ambiance de forêt"""
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)
    
    # Base de bruit vert (bruit filtré)
    base_noise = np.random.normal(0, 0.05, samples)
    
    # Chants d'oiseaux simulés
    bird_freqs = [1000, 2000, 3000, 4000]
    forest_sound = base_noise.copy()
    
    for freq in bird_freqs:
        # Oiseaux qui chantent de manière intermittente
        chirp_pattern = np.random.choice([0, 1], samples, p=[0.85, 0.15])
        bird_sound = 0.1 * np.sin(2 * np.pi * freq * t) * chirp_pattern
        forest_sound += bird_sound
    
    # Vent dans les feuilles
    wind_freq = 50
    wind_sound = 0.03 * np.sin(2 * np.pi * wind_freq * t)
    forest_sound += wind_sound
    
    return np.clip(forest_sound, -1, 1)

def generate_rain_ambiance(duration=60, sample_rate=44100):
    """Générer une ambiance de pluie"""
    samples = int(duration * sample_rate)
    
    # Bruit de pluie = bruit blanc filtré
    rain_noise = np.random.normal(0, 0.2, samples)
    
    # Filtrage pour simuler la pluie
    # Pluie légère = hautes fréquences, pluie forte = basses fréquences
    from scipy import signal
    # Filtre passe-bande pour simuler la pluie
    sos = signal.butter(4, [500, 8000], btype='band', fs=sample_rate, output='sos')
    filtered_rain = signal.sosfilt(sos, rain_noise)
    
    return np.clip(filtered_rain * 0.3, -1, 1)

def generate_ocean_ambiance(duration=60, sample_rate=44100):
    """Générer une ambiance d'océan"""
    samples = int(duration * sample_rate)
    t = np.linspace(0, duration, samples)
    
    # Base de bruit rose pour l'océan
    base_noise = np.random.normal(0, 0.1, samples)
    
    # Vagues (fréquences basses)
    wave_freq = 0.1  # Vagues lentes
    wave_sound = 0.3 * np.sin(2 * np.pi * wave_freq * t)
    
    # Variation des vagues
    wave_modulation = 0.2 * np.sin(2 * np.pi * 0.05 * t)
    wave_sound *= (1 + wave_modulation)
    
    # Bruit de l'eau
    water_noise = np.random.normal(0, 0.05, samples)
    
    ocean_sound = base_noise + wave_sound + water_noise
    
    return np.clip(ocean_sound, -1, 1)

def save_wave_file(filename, audio_data, sample_rate=44100):
    """Sauvegarder un fichier WAV"""
    # Convertir en 16-bit PCM
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

def create_sound_files():
    """Créer tous les fichiers audio"""
    print("Génération des fichiers audio...")
    
    # Créer le dossier sounds s'il n'existe pas
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
    
    sounds_to_generate = [
        ("white_noise.wav", generate_white_noise),
        ("cafe_ambiance.wav", generate_cafe_ambiance),
        ("forest_ambiance.wav", generate_forest_ambiance),
        ("rain_ambiance.wav", generate_rain_ambiance),
        ("ocean_ambiance.wav", generate_ocean_ambiance),
    ]
    
    for filename, generator_func in sounds_to_generate:
        filepath = os.path.join("sounds", filename)
        if not os.path.exists(filepath):
            print(f"Génération de {filename}...")
            try:
                audio_data = generator_func(duration=120)  # 2 minutes
                save_wave_file(filepath, audio_data)
                print(f"✓ {filename} créé avec succès")
            except Exception as e:
                print(f"✗ Erreur lors de la génération de {filename}: {e}")
        else:
            print(f"✓ {filename} existe déjà")
    
    print("\nGénération terminée!")

if __name__ == "__main__":
    try:
        from scipy import signal
        create_sound_files()
    except ImportError:
        print("Module scipy requis pour la génération audio.")
        print("Installation: pip install scipy")
