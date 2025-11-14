package br.com.integrador.service_busca_java.controller;

import br.com.integrador.service_busca_java.dto.SearchRequestDto;
import br.com.integrador.service_busca_java.dto.SearchResponseDto;
import br.com.integrador.service_busca_java.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/")
public class SearchController {

    @Autowired
    private SearchService searchService;

    /**
     * ENDPOINT 1: /build
     */
    @PostMapping("/build")
    public ResponseEntity<String> build(@RequestBody Map<String, double[]> centroids) {
        try {
            searchService.buildIndex(centroids);
            return ResponseEntity.ok("Índice construído com sucesso.");
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("Erro ao construir índice: " + e.getMessage());
        }
    }

    /**
     * ENDPOINT 2: /search
     */
    @PostMapping("/search")
    public ResponseEntity<SearchResponseDto> search(@RequestBody SearchRequestDto request) {
        try {
            // Usa o DTO de Request
            String closestCluster = searchService.findClosestCluster(request.getImageVector());
            // Retorna o DTO de Response
            return ResponseEntity.ok(new SearchResponseDto(closestCluster));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(null);
        }
    }
}