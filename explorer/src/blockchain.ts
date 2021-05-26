import axios from 'axios';
import { TBlock, TChain, TTransaction } from './Chain';

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

export const getBlockByHash = async (hash: string): Promise<TBlock| undefined> => {
    try {
        const response = await instance.get('block/'+hash);
        return JSON.parse(response.data);
    } catch (error) {
        console.error(error);
        return undefined
    }
}

export const getTransactionByHash = async (hash: string): Promise<TTransaction| undefined> => {
    try {
        const response = await instance.get('transaction/'+hash);
        return JSON.parse(response.data);
    } catch (error) {
        console.error(error);
        return undefined
    }
}