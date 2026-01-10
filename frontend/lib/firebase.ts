/**
 * Firebase client configuration for Google OAuth.
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, Auth } from 'firebase/auth';

// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSyAOh8zUvhxuVLavOK3Hav64kHSmcOjxeWc",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "learn-fastapi-auth.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "learn-fastapi-auth",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "learn-fastapi-auth.firebasestorage.app",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "627188126418",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:627188126418:web:8c1862415cc06bc1ec130b",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || "G-MRB1R7Z4ZL"
};

// Initialize Firebase (singleton pattern)
let app: FirebaseApp;
let auth: Auth;

function getFirebaseApp(): FirebaseApp {
  if (!app) {
    const existingApps = getApps();
    app = existingApps.length > 0 ? existingApps[0] : initializeApp(firebaseConfig);
  }
  return app;
}

function getFirebaseAuth(): Auth {
  if (!auth) {
    auth = getAuth(getFirebaseApp());
  }
  return auth;
}

/**
 * Sign in with Google using Firebase popup.
 * Returns the Firebase ID token to send to the backend.
 */
export async function signInWithGoogle(): Promise<string> {
  const auth = getFirebaseAuth();
  const provider = new GoogleAuthProvider();

  // Request email scope
  provider.addScope('email');
  provider.addScope('profile');

  const result = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();

  return idToken;
}

/**
 * Sign out from Firebase.
 */
export async function signOutFromFirebase(): Promise<void> {
  const auth = getFirebaseAuth();
  await auth.signOut();
}

export { getFirebaseAuth };
