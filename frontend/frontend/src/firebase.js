import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBBW1BJaMupNDLxWYab02ZRYhZZXclurAs",
  authDomain: "smartspend-ai-8f560.firebaseapp.com",
  projectId: "smartspend-ai-8f560",
  storageBucket: "smartspend-ai-8f560.firebasestorage.app",
  messagingSenderId: "545970423612",
  appId: "1:545970423612:web:beeb9debf9c554fb7ec039",
  measurementId: "G-TZG5XBFT01"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();