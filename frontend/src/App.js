import { useState } from "react";
import "./App.css";

function App() {

  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  // Upload document
  const uploadDocument = async () => {

    const formData = new FormData();

    formData.append("document", file);

    const response = await fetch(
      "http://127.0.0.1:5000/upload",
      {
        method: "POST",
        body: formData
      }
    );

    const data = await response.text();

    alert("Document Uploaded!");
  };

  // Ask question
  const askQuestion = async () => {

    const formData = new FormData();

    formData.append("question", question);

    const response = await fetch(
      "http://127.0.0.1:5000/ask",
      {
        method: "POST",
        body: formData
      }
    );

    const data = await response.json();

    setAnswer(data.answer);
  };

  return (
    <div className="container">

      <h1>AI Document Analyser</h1>

      <div className="upload-box">

        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button onClick={uploadDocument}>
          Upload
        </button>

      </div>

      <div className="question-box">

        <input
          type="text"
          placeholder="Ask question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button onClick={askQuestion}>
          Ask
        </button>

      </div>

      <div className="answer-box">

        <h3>Answer:</h3>

        <p>{answer}</p>

      </div>

    </div>
  );
}

export default App;