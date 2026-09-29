const $ = (id) =>
    document.getElementById(id);


let chatHistory = [];


// ---------------------------------------------------------
// NOTICE
// ---------------------------------------------------------

function notice(message) {

    const box = $("notice");

    box.textContent = message;

    box.classList.remove("hidden");

    setTimeout(() => {

        box.classList.add("hidden");

    }, 5000);
}


// ---------------------------------------------------------
// API HELPER
// ---------------------------------------------------------

async function api(
    url,
    options = {}
) {

    const response =
        await fetch(
            url,
            options
        );

    const data =
        await response
            .json()
            .catch(() => ({
                error:
                    "Invalid server response."
            }));

    if (!response.ok) {

        throw new Error(
            data.error ||
            "Request failed."
        );

    }

    return data;
}


// ---------------------------------------------------------
// ESCAPE HTML
// ---------------------------------------------------------

function escapeHtml(value) {

    return String(value)
        .replace(
            /[&<>'"]/g,
            character => {

                const entities = {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    "'": "&#39;",
                    '"': "&quot;",
                };

                return entities[
                    character
                ];
            }
        );
}


// ---------------------------------------------------------
// CHAT BUBBLE
// ---------------------------------------------------------

function addBubble(
    text,
    role
) {

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        `bubble ${role}`;

    bubble.textContent =
        text;

    $("chatMessages")
        .appendChild(
            bubble
        );

    $("chatMessages").scrollTop =
        $("chatMessages").scrollHeight;
}


// ---------------------------------------------------------
// NAVIGATION
// ---------------------------------------------------------

document
    .querySelectorAll(".nav-btn")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                document
                    .querySelectorAll(
                        ".nav-btn"
                    )
                    .forEach(item => {

                        item.classList.remove(
                            "active"
                        );

                    });


                button.classList.add(
                    "active"
                );


                document
                    .querySelectorAll(
                        ".tab-panel"
                    )
                    .forEach(panel => {

                        panel.classList.remove(
                            "active"
                        );

                    });


                const tab =
                    button.dataset.tab;

                $(tab)
                    .classList.add(
                        "active"
                    );


                $("pageTitle")
                    .textContent =
                    button.textContent
                        .replace(
                            /^\S+\s/,
                            ""
                        );


                if (tab === "history") {

                    loadHistory();

                }

            }
        );

    });


// ---------------------------------------------------------
// GENERIC TEXT REQUEST
// ---------------------------------------------------------

async function runText(
    endpoint,
    body,
    outputId
) {

    const output =
        $(outputId);

    output.textContent =
        "Thinking...";

    try {

        let options;

        /*
         * The summary API expects
         * multipart form data.
         */

        if (
            endpoint ===
            "/api/summarize"
        ) {

            options = {
                method: "POST",
                body: body,
            };

        } else {

            options = {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body:
                    JSON.stringify(body),
            };

        }

        const data =
            await api(
                endpoint,
                options
            );

        output.textContent =
            data.answer || "";

    } catch (error) {

        output.textContent =
            "Error: " +
            error.message;

    }

}


// ---------------------------------------------------------
// CHAT
// ---------------------------------------------------------

$("chatForm")
    .addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            const message =
                $("chatInput")
                    .value
                    .trim();

            if (!message) {
                return;
            }


            addBubble(
                message,
                "user"
            );


            $("chatInput").value =
                "";


            try {

                const data =
                    await api(
                        "/api/chat",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",
                            },

                            body:
                                JSON.stringify({
                                    message:
                                        message,

                                    history:
                                        chatHistory,
                                }),
                        }
                    );


                addBubble(
                    data.answer,
                    "ai"
                );


                chatHistory.push(
                    {
                        role: "user",
                        content: message,
                    },

                    {
                        role: "assistant",
                        content:
                            data.answer,
                    }
                );

            } catch (error) {

                addBubble(
                    "Error: " +
                    error.message,
                    "ai"
                );

            }

        }
    );


// ---------------------------------------------------------
// EXPLAIN
// ---------------------------------------------------------

$("exBtn")
    .addEventListener(
        "click",
        () => {

            const topic =
                $("exTopic")
                    .value
                    .trim();

            if (!topic) {

                notice(
                    "Please enter a topic."
                );

                return;
            }


            runText(
                "/api/explain",

                {
                    topic:
                        topic,

                    level:
                        $("exLevel")
                            .value,
                },

                "exOut"
            );

        }
    );


// ---------------------------------------------------------
// SUMMARY
// ---------------------------------------------------------

$("summaryBtn")
    .addEventListener(
        "click",
        () => {

            const text =
                $("summaryText")
                    .value
                    .trim();

            if (!text) {

                notice(
                    "Please paste your study notes first."
                );

                return;
            }


            const formData =
                new FormData();

            formData.append(
                "text",
                text
            );


            runText(
                "/api/summarize",
                formData,
                "summaryOut"
            );

        }
    );


// ---------------------------------------------------------
// PDF SUMMARY
// ---------------------------------------------------------

$("pdfFile")
    .addEventListener(
        "change",
        async () => {

            const file =
                $("pdfFile")
                    .files[0];

            if (!file) {
                return;
            }


            $("summaryOut")
                .textContent =
                "Reading PDF and generating summary...";


            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );


            try {

                const data =
                    await api(
                        "/api/upload-summary",
                        {
                            method: "POST",
                            body: formData,
                        }
                    );


                $("summaryOut")
                    .textContent =
                    `Pages: ${data.pages}\n\n${data.answer}`;

            } catch (error) {

                $("summaryOut")
                    .textContent =
                    "Error: " +
                    error.message;

            }

        }
    );


// ---------------------------------------------------------
// LEARNING PATH
// ---------------------------------------------------------

$("pathBtn")
    .addEventListener(
        "click",
        () => {

            const goal =
                $("pathGoal")
                    .value
                    .trim();

            if (!goal) {

                notice(
                    "Please enter your learning goal."
                );

                return;
            }


            runText(
                "/api/learning-path",

                {
                    goal:
                        goal,

                    level:
                        $("pathLevel")
                            .value,

                    weeks:
                        Number(
                            $("pathWeeks")
                                .value
                        ),
                },

                "pathOut"
            );

        }
    );


// ---------------------------------------------------------
// QUIZ
// ---------------------------------------------------------

$("quizBtn")
    .addEventListener(
        "click",
        async () => {

            const topic =
                $("quizTopic")
                    .value
                    .trim();

            if (!topic) {

                notice(
                    "Please enter a quiz topic."
                );

                return;
            }


            const output =
                $("quizOut");

            output.textContent =
                "Generating quiz...";


            try {

                const data =
                    await api(
                        "/api/quiz",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",
                            },

                            body:
                                JSON.stringify({

                                    topic:
                                        topic,

                                    count:
                                        Number(
                                            $("quizCount")
                                                .value
                                        ),

                                    difficulty:
                                        $("quizDifficulty")
                                            .value,

                                }),
                        }
                    );


                output.innerHTML =
                    "";


                data.questions
                    .forEach(
                        (question, index) => {

                            const card =
                                document
                                    .createElement(
                                        "div"
                                    );


                            card.className =
                                "q-card";


                            const title =
                                document
                                    .createElement(
                                        "b"
                                    );


                            title.textContent =
                                `${index + 1}. ${question.question}`;


                            card.appendChild(
                                title
                            );


                            question.options
                                .forEach(
                                    (
                                        option,
                                        optionIndex
                                    ) => {

                                        const label =
                                            document
                                                .createElement(
                                                    "label"
                                                );


                                        const radio =
                                            document
                                                .createElement(
                                                    "input"
                                                );


                                        radio.type =
                                            "radio";

                                        radio.name =
                                            `q${index}`;

                                        radio.value =
                                            optionIndex;


                                        label.appendChild(
                                            radio
                                        );


                                        label.appendChild(
                                            document
                                                .createTextNode(
                                                    " " +
                                                    option
                                                )
                                        );


                                        card.appendChild(
                                            label
                                        );

                                    }
                                );


                            const explanation =
                                document
                                    .createElement(
                                        "div"
                                    );


                            explanation.className =
                                "output quiz-answer";


                            explanation.style.display =
                                "none";


                            explanation.textContent =
                                `Answer: ${question.options[question.answer]}\n\n${question.explanation}`;


                            card.appendChild(
                                explanation
                            );


                            card.addEventListener(
                                "click",
                                () => {

                                    explanation.style.display =
                                        "block";

                                }
                            );


                            output.appendChild(
                                card
                            );

                        }
                    );

            } catch (error) {

                output.textContent =
                    "Error: " +
                    error.message;

            }

        }
    );


// ---------------------------------------------------------
// HISTORY
// ---------------------------------------------------------

async function loadHistory() {

    try {

        const data =
            await api(
                "/api/history"
            );


        if (
            !data.items ||
            data.items.length === 0
        ) {

            $("historyOut")
                .textContent =
                "No study activity yet.";

            return;
        }


        $("historyOut")
            .innerHTML =
            data.items
                .map(
                    item => {

                        return `
                            <div class="history-item">

                                <b>
                                    ${escapeHtml(
                                        item.feature
                                    )}
                                </b>

                                <small>
                                    ${escapeHtml(
                                        item.created_at
                                    )}
                                </small>

                                <div>
                                    ${escapeHtml(
                                        (
                                            item.input_text ||
                                            ""
                                        ).slice(0, 180)
                                    )}
                                </div>

                            </div>
                        `;

                    }
                )
                .join("");

    } catch (error) {

        $("historyOut")
            .textContent =
            error.message;

    }

}


// ---------------------------------------------------------
// LOGOUT
// ---------------------------------------------------------

const logoutButton =
    $("logoutBtn");

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        async () => {

            try {

                await api(
                    "/api/logout",
                    {
                        method: "POST",
                    }
                );

                window.location.href =
                    "/login";

            } catch (error) {

                notice(
                    error.message
                );

            }

        }
    );

}