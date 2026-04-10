/**
 * HUD_CORE Audio System
 * Procedural SFX using Web Audio API
 */

const HUDAudio = (() => {
    let audioCtx = null;
    let ambientOsc = null;
    let ambientGain = null;

    const init = () => {
        if (audioCtx) return;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        startAmbient();
    };

    const startAmbient = () => {
        // Low frequency hum
        ambientOsc = audioCtx.createOscillator();
        ambientGain = audioCtx.createGain();
        const filter = audioCtx.createBiquadFilter();

        ambientOsc.type = 'sawtooth';
        ambientOsc.frequency.setValueAtTime(55, audioCtx.currentTime); // A1 hum
        
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(100, audioCtx.currentTime);
        filter.Q.setValueAtTime(10, audioCtx.currentTime);

        ambientGain.gain.setValueAtTime(0.01, audioCtx.currentTime); // Very subtle

        ambientOsc.connect(filter);
        filter.connect(ambientGain);
        ambientGain.connect(audioCtx.destination);
        
        ambientOsc.start();
    };

    const playBeep = (freq = 880, duration = 0.05, type = 'sine') => {
        if (!audioCtx) return;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

        gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    };

    const playScan = () => {
        if (!audioCtx) return;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.type = 'square';
        osc.frequency.setValueAtTime(100, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(2000, audioCtx.currentTime + 1.0);

        gain.gain.setValueAtTime(0.02, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 1.0);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + 1.0);
    };

    return {
        init,
        beep: () => playBeep(880, 0.05),
        click: () => playBeep(440, 0.1, 'square'),
        error: () => playBeep(110, 0.3, 'sawtooth'),
        scan: playScan
    };
})();

// Attach to global window
window.HUDAudio = HUDAudio;

// Auto-init on first interaction (required by browsers)
window.addEventListener('mousedown', () => HUDAudio.init(), { once: true });
window.addEventListener('keydown', () => HUDAudio.init(), { once: true });
