import { createContext, useContext, useState, useEffect } from 'react';
import { authService, profileService } from '../services/authService';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchUser = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const data = await authService.getMe();
            setUser(data);
            try {
                const profileData = await profileService.getProfile();
                setProfile(profileData);
            } catch (pError) {
                console.warn("Failed to load profile", pError);
            }
        } catch (error) {
            console.error('Failed to fetch user', error);
            if (error.response && error.response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('token');
                setUser(null);
                setProfile(null);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            fetchUser();
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email, password) => {
        const data = await authService.login(email, password);
        localStorage.setItem('token', data.token);
        await fetchUser();
        return data;
    };

    const signup = async (name, email, password) => {
        const data = await authService.signup(name, email, password);
        localStorage.setItem('token', data.token);
        await fetchUser();
        return data;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        setProfile(null);
    };

    return (
        <UserContext.Provider value={{ user, profile, loading, login, signup, logout, fetchUser }}>
            {children}
        </UserContext.Provider>
    );
};

export const useUser = () => useContext(UserContext);
