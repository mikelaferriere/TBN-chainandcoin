import axios from 'axios';
import { TChain } from './Chain';

// Set config defaults when creating the instance
const instance = axios.create({
    baseURL: 'http://localhost:5000'
});

export const getFullChain = async (): Promise<TChain> => {
    try {
        const response = await instance.get('chain');
        return response.data;
    } catch (error) {
        console.error(error);
        return { chain: [], length: 0 }
    }
}