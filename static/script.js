// (c) 2026 shdown
// This code is licensed under MIT license (see LICENSE.MIT for details)

(() => {
    const parseSearchString = (search) => {
        const segments = search.slice(search.indexOf('?') + 1).split('&');
        const result = {};
        for (const segment of segments) {
            const [key, value] = segment.split('=', /*limit=*/2);
            if (value === undefined)
                continue;
            result[decodeURIComponent(key)] = decodeURIComponent(value);
        }
        return result;
    };

    const findDiv = (id) => {
        const res = document.getElementById(id);
        if (res === null) {
            throw new Error(`cannot find element by id "${id}"`);
        }
        return res;
    };

    const makeRequest = async (url, params) => {
        const data = new FormData();
        for (const [k, v] of Object.entries(params)) {
            data.append(k, v);
        }
        const respObj = await fetch(url, {
            method: 'POST',
            body: data,
        });
        if (!respObj.ok) {
            throw new Error(`Bad status: ${respObj.status} ${respObj.statusText}`);
        }
        const resp = await respObj.json();
        if (!resp.ok) {
            throw new Error(`Server returned error: ${resp.error_code} ${resp.error_msg}`);
        }
        return resp;
    };

    const divLoading = findDiv('loading');
    const divSwitch = findDiv('switch');
    const divDecodedText = findDiv('decoded_text');
    const divResult = findDiv('result');

    const htmlsForSwitchStates = {
        'ready': '<span class="sw_ready">☛ Нажмите и говорите ☚</span>',
        'rec_new': '<span class="sw_pending">Начинаю запись…</span>',
        'rec_wait': '<span class="sw_speak">• Говорите…</span>',
        'exec_cmd': '<span class="sw_pending">Выполняю команду…</span>',
        'gen_uid': '<span class="sw_pending">Подождите…</span>',
        'cas': '<span class="sw_pending">Подождите…</span>',
    };

    let switchState;

    const setSwitchState = (state) => {
        switchState = state;
        divSwitch.innerHTML = htmlsForSwitchStates[state];
    };

    const setDecodedText = (text) => {
        if (text === null) {
            divDecodedText.innerText = '(тишина)';
            divDecodedText.className = 'cls_light';
        } else {
            divDecodedText.innerText = text;
            divDecodedText.className = '';
        }
    };

    const setResultOk = (found, output) => {
        if (!found) {
            divResult.innerText = '(команда не найдена)';
            divResult.className = 'cls_light';
        } else if (output === null) {
            divResult.innerText = '✔ Команда выполнена';
            divResult.className = 'cls_ok';
        } else {
            divResult.innerText = output;
            divResult.className = '';
        }
    };

    const setResultError = (msg) => {
        divResult.innerText = '✘ Ошибка: ' + msg;
        divResult.className = 'cls_error';
    };

    const cleanUpText = (origText) => {
        let text = origText;
        text = text.replaceAll(/[.!?,:;]/g, ' ');
        text = text.replaceAll(/\s+/g, ' ');
        text = text.trim();
        return text;
    };

    const startRecordingNow = async (uid) => {
        setSwitchState('rec_new');
        const respRec = await makeRequest('/api/recording/new', {
            uid: uid,
        });

        setSwitchState('rec_wait');
        const respWait = await makeRequest('/api/recording/wait', {
            uid: uid,
        });

        if (respWait.text === null) {
            setDecodedText(null);
            setSwitchState('ready');
            return;
        }
        setDecodedText(respWait.text);

        const text = cleanUpText(respWait.text);
        if (text === '') {
            setDecodedText(null);
            setSwitchState('ready');
            return;
        }

        setSwitchState('exec_cmd');
        const respExec = await makeRequest('/api/command', {
            text: text,
        });

        setResultOk(respExec.found, respExec.result);
        setSwitchState('ready');
    };

    const startRecordingAfterClick = async () => {
        setSwitchState('gen_uid');
        const respUID = await makeRequest('/api/uid/new', {});
        await startRecordingNow(respUID.uid);
    };

    setSwitchState('ready');

    divSwitch.addEventListener('click', () => {
        if (switchState !== 'ready') {
            return;
        }
        startRecordingAfterClick().catch((e) => {
            setResultError(e.toString());
            setSwitchState('ready');
        });
    });

    const casAndThenRecord = async (uid) => {
        setSwitchState('cas');
        await makeRequest('/api/uid/pending/cas', {
            old_uid: uid,
            new_uid: '#',
        });
        await startRecordingNow(uid);
    };

    const searchParams = parseSearchString(location.search);
    if (searchParams.quick_run_uid) {
        casAndThenRecord(searchParams.quick_run_uid).catch((e) => {
            setResultError(e.toString());
            setSwitchState('ready');
        });
    }

    divLoading.hidden = true;
})();
