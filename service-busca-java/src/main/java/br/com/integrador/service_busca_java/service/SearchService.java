package br.com.integrador.service_busca_java.service;

import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Service
public class SearchService {

    // A Estrutura de Dados (Tabela de Hash) exigida
    private final Map<String, double[]> clusterIndex = new HashMap<>();

    /**
     * Constrói o índice (endpoint /build)
     */
    public void buildIndex(Map<String, double[]> centroids) {
        clusterIndex.clear();
        clusterIndex.putAll(centroids);
        System.out.println("Índice de clusters construído com " + clusterIndex.size() + " entradas.");
    }

    /**
     * Encontra o cluster mais próximo (endpoint /search)
     */
    public String findClosestCluster(double[] imageVector) {
        if (clusterIndex.isEmpty()) {
            throw new IllegalStateException("O índice de clusters não foi construído.");
        }

        String bestCluster = "";
        double minDistance = Double.MAX_VALUE;

        // Itera na Tabela de Hash
        for (Map.Entry<String, double[]> entry : clusterIndex.entrySet()) {
            String clusterName = entry.getKey();
            double[] centroidVector = entry.getValue();

            double distance = calculateEuclideanDistance(imageVector, centroidVector);

            if (distance < minDistance) {
                minDistance = distance;
                bestCluster = clusterName;
            }
        }
        System.out.println("Busca: Vetor mais próximo do cluster '" + bestCluster + "'");
        return bestCluster;
    }

    /**
     * Função de cálculo de Distância Euclidiana
     */
    private double calculateEuclideanDistance(double[] v1, double[] v2) {
        double sum = 0.0;
        for (int i = 0; i < v1.length; i++) {
            sum += Math.pow(v1[i] - v2[i], 2);
        }
        return Math.sqrt(sum);
    }
}