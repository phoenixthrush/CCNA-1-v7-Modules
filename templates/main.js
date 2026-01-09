// Fisher–Yates shuffle
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
let currentIndex = 0;
let answered = false;

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

        questions = shuffle(data).map(q => ({
            ...q,
            options: Array.isArray(q.options) ? shuffle(q.options) : []
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
    nextBtn.textContent = 'Submit';

    if (currentIndex >= questions.length) {
        return showError('No more questions.');
    }

    const q = questions[currentIndex];
    const wrapper = createEl('div');

    wrapper.appendChild(createEl('p', { textContent: q.question || q.title || `Item ${currentIndex + 1}` }));

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

    if (chosen.length === 0) {
        resultMsg.textContent = 'Please choose an answer.';
        return;
    }

    const correct = chosen.length === q.correct_answers.length &&
        chosen.every(a => q.correct_answers.includes(a));

    inputs.forEach(i => i.disabled = true);

    if (!correct) {
        markAnswers(q, chosen);
        resultMsg.textContent = 'Wrong!';
        explanationMsg.style.display = 'block';
        explanationMsg.textContent = q.explanation || 'No explanation available for this question.';
        nextBtn.textContent = 'Continue';
    } else {
        resultMsg.textContent = 'Correct!';
    }

    answered = true;
});

function markAnswers(q, chosen) {
    q.options.forEach((opt, index) => {
        const li = document.getElementById(`li-${index}`);
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

loadQuestions();