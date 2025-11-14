package br.com.integrador.service_busca_java.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor // Cria um construtor
public class SearchResponseDto {
    private String clusterEncontrado;
}