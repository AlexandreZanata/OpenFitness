package com.openfitness.application.usecase.bootstrap

import com.openfitness.domain.repository.CatalogSeeder

class SeedCatalogUseCase(
    private val catalogSeeder: CatalogSeeder,
) {
    suspend operator fun invoke() {
        catalogSeeder.seedIfEmpty()
    }
}
