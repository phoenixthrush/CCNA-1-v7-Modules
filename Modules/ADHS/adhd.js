/*
    Do not add index.html?adhd=1 :)
*/

(function () {
    const STYLE_ID = 'adhd-style';
    const ROOT_ID = 'adhd-videos-root';

    const SCRIPT_SRC = (() => {
        const cs = document.currentScript;
        if (cs && cs.tagName === 'SCRIPT' && cs.src) return cs.src;

        const scripts = document.getElementsByTagName('script');
        for (let i = scripts.length - 1; i >= 0; i--) {
            const s = scripts[i];
            if (s && s.src && /(^|\/|\\)adhd\.js(\?|#|$)/i.test(s.src)) return s.src;
        }

        return '';
    })();

    function isEnabledByUrl() {
        try {
            const sp = new URLSearchParams(window.location.search);
            if (!sp.has('adhd')) return false;

            const raw = sp.get('adhd');
            if (raw === null || raw.trim() === '') return true;

            const v = raw.trim().toLowerCase();
            if (['0', 'false', 'off', 'no'].includes(v)) return false;
            if (['1', 'true', 'on', 'yes'].includes(v)) return true;

            return true;
        } catch {
            return false;
        }
    }

    function getScriptBaseUrl() {
        if (!SCRIPT_SRC) return null;
        return new URL('./', SCRIPT_SRC);
    }

    function addStyleOnce() {
        if (document.getElementById(STYLE_ID)) return;

        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = `
.video-container {
    position: absolute;
    border: 3px solid black;

    width: 15%;
    height: auto;
    display: flex;
    justify-content: center;
    align-items: flex-end;
    z-index: 9999;
}

.subway {
    margin-right: 15px;
    margin-bottom: 20px;
    right: 0;
    bottom: 0;
}

.minecraft {
    margin-left: 15px;
    margin-bottom: 20px;
    left: 0;
    bottom: 0;
}

.asmr {
    margin-right: 15px;
    margin-top: 20px;
    right: 0;
    top: 0;
}

.fireplace {
    margin-left: 15px;
    margin-top: 20px;
    left: 0;
    top: 0;
}

.video-container video {
    width: 100%;
    height: auto;
}
        `.trim();

        (document.head || document.documentElement).appendChild(style);
    }

    function createVideo(srcUrl) {
        const video = document.createElement('video');
        video.src = srcUrl;
        video.muted = true;
        video.autoplay = true;
        video.loop = true;
        video.playsInline = true;
        video.preload = 'metadata';
        video.setAttribute('muted', '');
        video.setAttribute('autoplay', '');
        video.setAttribute('loop', '');
        video.setAttribute('playsinline', '');
        return video;
    }

    function addVideosOnce() {
        if (document.getElementById(ROOT_ID)) return;

        const base = getScriptBaseUrl();
        if (!base) return;

        const root = document.createElement('div');
        root.id = ROOT_ID;

        const subway = document.createElement('div');
        subway.className = 'video-container subway';
        subway.appendChild(createVideo(new URL('subway_surfers.mp4', base).href));

        const minecraft = document.createElement('div');
        minecraft.className = 'video-container minecraft';
        minecraft.appendChild(createVideo(new URL('minecraft.mp4', base).href));

        const asmr = document.createElement('div');
        asmr.className = 'video-container asmr';
        asmr.appendChild(createVideo(new URL('asmr.mp4', base).href));

        const fireplace = document.createElement('div');
        fireplace.className = 'video-container fireplace';
        const inner = document.createElement('div');
        inner.appendChild(createVideo(new URL('fireplace.mp4', base).href));
        inner.appendChild(document.createElement('br'));
        inner.appendChild(createVideo(new URL('feet.mp4', base).href));
        fireplace.appendChild(inner);

        root.appendChild(subway);
        root.appendChild(minecraft);
        root.appendChild(asmr);
        root.appendChild(fireplace);

        const nextBtn = document.getElementById('next-btn');
        if (nextBtn && nextBtn.parentNode) {
            nextBtn.insertAdjacentElement('afterend', root);
            return;
        }

        (document.body || document.documentElement).appendChild(root);
    }

    function init() {
        if (!isEnabledByUrl()) return;
        addStyleOnce();
        addVideosOnce();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();