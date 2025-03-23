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

            // Clear previous answer options or audio player
            document.getElementById("answer-container").innerHTML = '';
            document.getElementById("feedback").innerText = '';

            // Check if the mode is "listen_and_choose"
            if (mode === "listen_and_choose") {
                if (data.audio) {
                    // Create an audio element for listening mode
                    const audioElement = document.createElement("audio");
                    audioElement.setAttribute("controls", "");
                    audioElement.setAttribute("src", data.audio); // Set the audio source
                    document.getElementById("answer-container").appendChild(audioElement);
                } else {
                    // If no audio, provide feedback
                    document.getElementById("feedback").innerText = "No audio available for this word.";
                }

                // Display the multiple-choice options
                displayMultipleChoice(data.choices);
            } else if (mode === "multiple_choice") {
                // Show multiple-choice buttons in the multiple-choice mode
                displayMultipleChoice(data.choices);
            } else if (mode === "written") {
                // Show written input if mode is written
                displayWrittenInput();
            }
        }
    });
}

function displayMultipleChoice(choices) {
    const container = document.getElementById("answer-container");

    choices.forEach(choice => {
        const button = document.createElement("button");
        button.innerText = choice;
        button.onclick = function () {
            if (choice === correctAnswer) {
                document.getElementById("feedback").innerText = "Correct!";
            } else {
                document.getElementById("feedback").innerText = "Incorrect. Try again!";
            }
        };
        container.appendChild(button);
    });
}

function displayWrittenInput() {
    let answerContainer = document.getElementById("answer-container");
    answerContainer.innerHTML = `
        <input type="text" id="answer" placeholder="Type your answer">
        <button onclick="submitAnswer()">Submit</button>
    `;
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
