async function askQuestion() {

    const question = document.getElementById("question").value;

    const formData = new FormData();

    formData.append("question", question);

    const response = await fetch("/ask", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    document.getElementById("answer-box").innerHTML = `
        <h3>Answer:</h3>
        <p>${data.answer}</p>
    `;
}