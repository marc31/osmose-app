describe('datasets page', () => {
  beforeEach(() => {
    cy.login("admin", "osmose29")
    cy.visit('http://localhost:3000/')
  })

  it('displays 5 datasets by default', () => {
    cy.get('tr').should('have.length', 6)
  })
})