import "./App.css";
// @ts-ignore
import Browse from "@components/Browser";
import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Browse />} />
      </Routes>
    </BrowserRouter   >
  );
}

export default App;
