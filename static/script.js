let correctAnswer = "";

function startQuiz() {
    let category = document.getElementById("category").value;
    let mode = document.getElementById("mode").value; // Get the answer mode

    fetch("/get_question", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: category, mode: mode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            document.getElementById("question").innerText = `Translate: ${data.afghan_word}`;
            correctAnswer = data.correct_translation;

            // Check if multiple-choice mode is selected
            if (mode === "multiple_choice") {
                displayMultipleChoice(data.choices);
            } else {
                displayWrittenInput();
            }
        }
    });
}

function displayMultipleChoice(choices) {
    let answerContainer = document.getElementById("answer-container");
    answerContainer.innerHTML = ""; // Clear previous answers

    choices.forEach(choice => {
        let button = document.createElement("button");
        button.innerText = choice;
        button.onclick = function () { checkAnswer(choice); };
        answerContainer.appendChild(button);
    });
}

function displayWrittenInput() {
    let answerContainer = document.getElementById("answer-container");
    answerContainer.innerHTML = `
        <input type="text" id="answer" placeholder="Type your answer">
        <button onclick="submitAnswer()">Submit</button>
    `;
}

function checkAnswer(userAnswer) {
    let feedback = document.getElementById("feedback");
    if (userAnswer === correctAnswer) {
        feedback.innerText = "Correct!";
        feedback.style.color = "green";
    } else {
        feedback.innerText = `Incorrect! The correct answer was: ${correctAnswer}`;
        feedback.style.color = "red";
    }
}

function submitAnswer() {
    let userAnswer = document.getElementById("answer").value.trim().toLowerCase();
    let feedback = document.getElementById("feedback");

    if (userAnswer === correctAnswer.toLowerCase()) {
        feedback.innerText = "Correct!";
        feedback.style.color = "green";
    } else {
        feedback.innerText = `Incorrect! The correct answer was: ${correctAnswer}`;
        feedback.style.color = "red";
    }
}
