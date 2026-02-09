const ALLOW_SKIP = true;

function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

const container = document.getElementById('questions-container');
const nextBtn = document.getElementById('next-btn');

let questions = [];
let originalQuestions = [];

let currentIndex = 0;
let answered = false;

let correctCount = 0;
let answeredCount = 0;
let skippedCount = 0;

function sanitizeQuestions(data) {
    const seen = new Set();
    const cleaned = [];

    for (const item of data) {
        if (!item || typeof item.question !== 'string') continue;

        const question = item.question.trim();
        if (!question) continue;

        const optionsRaw = Array.isArray(item.options)
            ? item.options.filter(o => typeof o === 'string')
            : [];
        const options = optionsRaw.map(o => o.trim()).filter(o => o.length > 0);

        const optMap = new Map(options.map(o => [o.toLowerCase(), o]));

        const corrRaw = Array.isArray(item.correct_answers)
            ? item.correct_answers.filter(o => typeof o === 'string')
            : [];

        let correct = [];
        for (const c of corrRaw) {
            const cTrim = c.trim();
            if (!cTrim) continue;

            if (options.includes(cTrim)) {
                correct.push(cTrim);
                continue;
            }

            const mapped = optMap.get(cTrim.toLowerCase());
            if (mapped) correct.push(mapped);
        }

        correct = [...new Set(correct)];

        if (options.length === 0 || correct.length === 0) continue;

        const key = question.toLowerCase().replace(/\s+/g, ' ');
        if (seen.has(key)) continue;

        seen.add(key);
        cleaned.push({ ...item, question, options, correct_answers: correct });
    }

    return cleaned;
}

async function loadQuestions() {
    try {
        const rawJson = `
            {{ JSON_CONTENT }}
        `;

        let data;

        try {
            data = JSON.parse(rawJson);
        } catch (e) {
            return showError('Invalid embedded JSON.');
        }

        if (!Array.isArray(data)) {
            return showError('Invalid JSON: expected an array of questions.');
        }

        data = sanitizeQuestions(data);

        originalQuestions = data.map(q => ({
            ...q,
            options: Array.isArray(q.options) ? [...q.options] : []
        }));

        questions = shuffle(originalQuestions).map(q => ({
            ...q,
            options: Array.isArray(q.options) ? shuffle([...q.options]) : []
        }));

        showQuestion();
    } catch (err) {
        showError('Error loading JSON: ' + err.message);
        console.error(err);
    }
}

function showError(msg) {
    container.textContent = msg;
}

function createEl(tag, props = {}, children = []) {
    const el = document.createElement(tag);
    Object.assign(el, props);
    children.forEach(child => el.appendChild(child));
    return el;
}

function showQuestion() {
    container.innerHTML = '';
    answered = false;

    nextBtn.onclick = null;
    nextBtn.disabled = false;
    nextBtn.textContent = 'Submit';

    if (currentIndex >= questions.length) {
        showFinalSummary();
        return;
    }

    const q = questions[currentIndex];
    const wrapper = createEl('div');

    const titleLine = q.title ? ("\n" + q.title) : "";
    wrapper.appendChild(createEl('p', { textContent: (q.question || q.title || `Item ${currentIndex + 1}`) + titleLine }));

    if (q.image_url) wrapper.appendChild(createImageBlock(q.image_url));

    wrapper.appendChild(createOptionsList(q));

    wrapper.appendChild(createEl('p', { id: 'explanation-msg', style: 'display:none;' }));
    wrapper.appendChild(createEl('p', { id: 'result-msg' }));
    wrapper.appendChild(createEl('div', {
        className: 'question-counter',
        textContent: `${currentIndex + 1} / ${questions.length}`
    }));

    container.appendChild(wrapper);
}

function createImageBlock(url) {
    const loader = createEl('div', {
        className: 'image-loader',
        id: 'main-loader',
        textContent: 'Loading image...'
    });

    const img = createEl('img', {
        src: url,
        style: 'max-width:100%;max-height:500px;margin-bottom:20px;display:none;'
    });

    img.onload = () => {
        loader.style.display = 'none';
        img.style.display = 'block';
    };

    img.onerror = () => {
        loader.textContent = 'Failed to load image';
        loader.style.color = '#ef4444';
    };

    return createEl('div', {}, [loader, img]);
}

function createOptionsList(q) {
    const list = createEl('ul');
    const isMultiple = q.correct_answers?.length > 1;

    q.options.forEach((opt, i) => {
        const li = createEl('li', { id: `li-${i}` });
        const input = createEl('input', {
            type: isMultiple ? 'checkbox' : 'radio',
            name: 'answer',
            value: opt,
            id: `opt-${i}`
        });

        let label;

        if (isImage(opt)) {
            input.dataset.isImage = 'true';
            label = createImageOption(opt, i);
        } else {
            label = createEl('label', { htmlFor: `opt-${i}`, textContent: opt });
        }

        li.appendChild(input);
        li.appendChild(label);
        list.appendChild(li);
    });

    list.querySelectorAll('input[data-is-image="true"]').forEach(i => i.checked = true);

    return list;
}

function isImage(opt) {
    return typeof opt === 'string' &&
        (opt.endsWith('.png') || opt.endsWith('.jpg') || opt.endsWith('.jpeg') || opt.startsWith('http'));
}

function createImageOption(url, index) {
    const loader = createEl('div', {
        className: 'image-loader',
        id: `loader-${index}`,
        textContent: 'Loading image...'
    });

    const img = createEl('img', {
        src: url,
        style: 'max-width:100%;max-height:300px;margin-top:10px;cursor:pointer;display:none;'
    });

    img.onload = () => {
        loader.style.display = 'none';
        img.style.display = 'block';
    };

    img.onerror = () => {
        loader.textContent = 'Failed to load image';
        loader.style.color = '#ef4444';
    };

    return createEl('label', { htmlFor: `opt-${index}` }, [loader, img]);
}

nextBtn.addEventListener('click', () => {
    const q = questions[currentIndex];
    const inputs = [...document.querySelectorAll('input[name="answer"]')];
    const resultMsg = document.getElementById('result-msg');
    const explanationMsg = document.getElementById('explanation-msg');

    if (answered) {
        currentIndex++;
        showQuestion();
        return;
    }

    const chosen = inputs.filter(i => i.checked).map(i => i.value);

    if (chosen.length === 0 && ALLOW_SKIP) {
        answeredCount++;
        skippedCount++;

        inputs.forEach(i => i.disabled = true);

        if (resultMsg) resultMsg.textContent = 'Skipped';
        nextBtn.textContent = 'Continue';
        answered = true;
        return;
    }

    if (chosen.length === 0) {
        if (resultMsg) resultMsg.textContent = 'Please choose an answer.';
        return;
    }

    const correct = chosen.length === q.correct_answers.length &&
        chosen.every(a => q.correct_answers.includes(a));

    inputs.forEach(i => i.disabled = true);

    answeredCount++;

    if (!correct) {
        markAnswers(q, chosen);

        if (resultMsg) resultMsg.textContent = 'Wrong!';
        if (explanationMsg) {
            explanationMsg.style.display = 'block';
            explanationMsg.textContent = q.explanation || 'No explanation available for this question.';
        }
        nextBtn.textContent = 'Continue';
    } else {
        correctCount++;
        if (resultMsg) resultMsg.textContent = 'Correct!';
    }

    answered = true;
});

function markAnswers(q, chosen) {
    q.options.forEach((opt, index) => {
        const li = document.getElementById(`li-${index}`);
        if (!li) return;

        const isCorrect = q.correct_answers.includes(opt);
        const isChosen = chosen.includes(opt);

        if (isCorrect) {
            li.classList.add('correct-answer');
            li.style.color = '#8bc34a';
        }
        if (isChosen && !isCorrect) {
            li.classList.add('wrong-answer');
        }
    });
}

document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.code === 'Enter') {
        e.preventDefault();
        nextBtn.click();
        return;
    }

    const index = (e.key === '0') ? 9 : Number(e.key) - 1;
    if (index < 0 || index > 9) return;

    const li = document.getElementById(`li-${index}`);
    if (!li) return;

    const label = li.querySelector('label');
    if (label) {
        e.preventDefault();
        label.click();
    }
});

function showFinalSummary() {
    const total = questions.length;
    const percent = total > 0 ? Math.round((correctCount / total) * 100) : 0;

    container.innerHTML = '';
    const summary = createEl('div');

    const headline = createEl('p', { textContent: 'Results' });
    const details = createEl('p', {
        textContent: `Correct: ${correctCount} of ${total}  •  ${percent}%  •  Skipped: ${skippedCount}`
    });

    const btnBar = createEl('div', { className: 'summary-actions' });

    const restart = createEl('button', { textContent: 'Restart' });
    restart.addEventListener('click', restartQuiz);

    const review = createEl('button', { textContent: 'Review answers' });
    review.addEventListener('click', reviewAll);

    btnBar.appendChild(restart);
    btnBar.appendChild(review);

    summary.appendChild(headline);
    summary.appendChild(details);
    summary.appendChild(btnBar);

    container.appendChild(summary);

    nextBtn.textContent = 'Done';
    nextBtn.disabled = true;
    nextBtn.onclick = null;
}

function restartQuiz() {
    correctCount = 0;
    answeredCount = 0;
    skippedCount = 0;
    currentIndex = 0;
    answered = false;

    questions = shuffle(originalQuestions).map(q => ({
        ...q,
        options: Array.isArray(q.options) ? shuffle([...q.options]) : []
    }));

    container.innerHTML = '';
    nextBtn.disabled = false;
    nextBtn.textContent = 'Submit';
    nextBtn.onclick = null;

    showQuestion();
}

function reviewAll() {
    container.innerHTML = '';

    const listWrap = createEl('div');

    questions.forEach((q, qi) => {
        const block = createEl('div', { className: 'review-block' });

        block.appendChild(createEl('p', { textContent: `Question ${qi + 1}: ${q.question}` }));

        const ul = createEl('ul');

        (q.options || []).forEach((opt) => {
            const li = createEl('li');

            const isCorrect = (q.correct_answers || []).includes(opt);
            const lab = createEl('label', {
                textContent: opt,
                style: isCorrect ? 'border-color:#8bc34a; color:#8bc34a; font-weight:600;' : ''
            });

            li.appendChild(lab);
            ul.appendChild(li);
        });

        block.appendChild(ul);

        if (q.explanation) {
            block.appendChild(createEl('p', {
                textContent: q.explanation,
                className: 'review-explanation'
            }));
        }

        listWrap.appendChild(block);
    });

    container.appendChild(listWrap);

    nextBtn.disabled = false;
    nextBtn.textContent = 'Back';

    nextBtn.onclick = () => {
        nextBtn.onclick = null;
        showFinalSummary();
        nextBtn.disabled = true;
    };
}

loadQuestions();