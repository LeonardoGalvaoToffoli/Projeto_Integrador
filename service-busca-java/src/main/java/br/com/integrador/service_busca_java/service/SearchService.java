package br.com.integrador.service_busca_java.service;

import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

@Service
public class SearchService {

    /*
     * Estrutura de Dados: Tabela de Hash (HashMap).
     * Utilizada para armazenar e indexar os centróides dos clusters.
     * Permite associação direta entre o identificador do cluster e seu vetor característico.
     */
    private final Map<String, double[]> clusterIndex = new HashMap<>();

    /**
     * Constrói o índice em memória a partir dos dados fornecidos pelo processamento Python.
     */
    public void buildIndex(Map<String, double[]> centroids) {
    clusterIndex.clear();
    clusterIndex.putAll(centroids);
    
    System.out.println("=== CONTEÚDO DA TABELA HASH ===");
    clusterIndex.forEach((nome, vetor) -> {
        System.out.println("Chave (Hash): " + nome + " -> Valor (Vetor): [ " + vetor[0] + ", ... ]");
    });
    System.out.println("===============================");
}

    /**
     * Executa a busca pelo cluster mais próximo (Nearest Neighbor Search).
     * Utiliza a distância Euclidiana para comparar o vetor da imagem de entrada
     * com os centróides armazenados.
     */
    public String findClosestCluster(double[] imageVector) {
        if (clusterIndex.isEmpty()) {
            throw new IllegalStateException("Índice não inicializado.");
        }

        String bestCluster = "";
        double minDistance = Double.MAX_VALUE;

        // Itera sobre os clusters para calcular a distância mínima
        for (Map.Entry<String, double[]> entry : clusterIndex.entrySet()) {
            String clusterName = entry.getKey();
            double[] centroidVector = entry.getValue();

            double distance = calculateEuclideanDistance(imageVector, centroidVector);

            if (distance < minDistance) {
                minDistance = distance;
                bestCluster = clusterName;
            }
        }
        System.out.println("Busca finalizada. Resultado: " + bestCluster);
        return bestCluster;
    }

    /**
     * Cálculo da Distância Euclidiana entre dois vetores n-dimensionais.
     * d(p,q) = sqrt(sum((pi - qi)^2))
     */
    private double calculateEuclideanDistance(double[] v1, double[] v2) {
        double sum = 0.0;
        for (int i = 0; i < v1.length; i++) {
            sum += Math.pow(v1[i] - v2[i], 2);
        }
        return Math.sqrt(sum);
    }
}